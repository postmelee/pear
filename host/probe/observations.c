#include "observations.h"

#include <CoreFoundation/CoreFoundation.h>
#include <Security/Security.h>
#include <dlfcn.h>
#include <errno.h>
#include <inttypes.h>
#include <mach/machine.h>
#include <mach-o/dyld.h>
#include <mach-o/loader.h>
#include <string.h>
#include <sys/sysctl.h>
#include <unistd.h>

const char *const pear_symbol_names[PEAR_SYMBOL_COUNT] = {
    "os_set_custom_x18_abi_enabled",
    "os_custom_x18_abi_enabled",
    "posix_spawnattr_set_4k_page_size_np",
    "thread_set_x86_64_compat"
};

pear_observation pear_observation_error(pear_value_kind kind, pear_status status,
                                      pear_error_domain domain, int64_t code)
{
    pear_observation result = {0};
    result.kind = kind;
    result.status = status;
    result.error_domain = domain;
    result.error_code = code;
    return result;
}

static pear_observation invalid(pear_value_kind kind, int code)
{
    return pear_observation_error(kind, PEAR_FAILED, PEAR_ERROR_INTERNAL, code);
}

pear_observation pear_observed_text(const char *value)
{
    pear_observation result = {0};
    result.kind = PEAR_TEXT;
    if (value == NULL) return invalid(PEAR_TEXT, EINVAL);
    size_t length = strnlen(value, PEAR_TEXT_CAPACITY);
    if (length == PEAR_TEXT_CAPACITY) return invalid(PEAR_TEXT, EOVERFLOW);
    memcpy(result.text, value, length + 1);
    result.status = PEAR_OBSERVED;
    return result;
}

pear_observation pear_observed_integer(int64_t value)
{
    pear_observation result = {0};
    result.kind = PEAR_INTEGER;
    result.status = PEAR_OBSERVED;
    result.number = value;
    return result;
}

pear_observation pear_observed_boolean(bool value)
{
    pear_observation result = pear_observed_integer(value ? 1 : 0);
    result.kind = PEAR_BOOLEAN;
    return result;
}

static pear_observation errno_result(pear_value_kind kind, int code)
{
    pear_status status = (code == EPERM || code == EACCES || code == ENOENT ||
                          code == ENOTSUP || code == ENOSYS)
                             ? PEAR_UNAVAILABLE : PEAR_FAILED;
    return pear_observation_error(kind, status, PEAR_ERROR_ERRNO, code);
}

static bool valid_utf8(const char *text)
{
    size_t length = strnlen(text, PEAR_TEXT_CAPACITY);
    if (length == PEAR_TEXT_CAPACITY) return false;
    for (size_t i = 0; i < length;) {
        unsigned char first = (unsigned char)text[i++];
        if (first < 0x80) continue;
        uint32_t codepoint;
        unsigned remaining;
        uint32_t minimum;
        if (first >= 0xc2 && first <= 0xdf) {
            codepoint = first & 0x1f; remaining = 1; minimum = 0x80;
        } else if (first >= 0xe0 && first <= 0xef) {
            codepoint = first & 0x0f; remaining = 2; minimum = 0x800;
        } else if (first >= 0xf0 && first <= 0xf4) {
            codepoint = first & 0x07; remaining = 3; minimum = 0x10000;
        } else return false;
        if (remaining > length - i) return false;
        while (remaining-- > 0) {
            unsigned char next = (unsigned char)text[i++];
            if ((next & 0xc0) != 0x80) return false;
            codepoint = (codepoint << 6) | (next & 0x3f);
        }
        if (codepoint < minimum || codepoint > 0x10ffff ||
            (codepoint >= 0xd800 && codepoint <= 0xdfff)) return false;
    }
    return true;
}

static pear_observation checked(pear_observation value, pear_value_kind kind)
{
    if (value.kind != kind || value.status < PEAR_UNAVAILABLE ||
        value.status > PEAR_FAILED) return invalid(kind, EINVAL);
    if (value.status == PEAR_OBSERVED) {
        if (value.error_domain != PEAR_ERROR_NONE || value.error_code != 0)
            return invalid(kind, EINVAL);
        if (kind == PEAR_TEXT && !valid_utf8(value.text))
            return invalid(kind, EILSEQ);
        if (kind == PEAR_BOOLEAN && value.number != 0 && value.number != 1)
            return invalid(kind, EPROTO);
    } else if (value.error_domain < PEAR_ERROR_ERRNO ||
               value.error_domain > PEAR_ERROR_INTERNAL) {
        return invalid(kind, EINVAL);
    }
    return value;
}

static pear_observation system_architecture(void *context)
{
    (void)context;
    const struct mach_header *header = _dyld_get_image_header(0);
    if (header == NULL) return invalid(PEAR_TEXT, ENOENT);
    if (header->magic != MH_MAGIC_64 || header->filetype != MH_EXECUTE)
        return invalid(PEAR_TEXT, EPROTO);
    if (header->cputype == CPU_TYPE_ARM64) {
        cpu_subtype_t subtype = header->cpusubtype & ~CPU_SUBTYPE_MASK;
        return pear_observed_text(subtype == CPU_SUBTYPE_ARM64E ? "arm64e" : "arm64");
    }
    if (header->cputype == CPU_TYPE_X86_64) return pear_observed_text("x86_64");
    return errno_result(PEAR_TEXT, ENOTSUP);
}

static pear_observation system_sysctl_text(void *context, const char *name)
{
    (void)context;
    char value[PEAR_TEXT_CAPACITY] = {0};
    size_t size = sizeof(value);
    if (sysctlbyname(name, value, &size, NULL, 0) != 0)
        return errno_result(PEAR_TEXT, errno);
    if (size == 0 || size > sizeof(value) || value[size - 1] != '\0' ||
        strnlen(value, size) != size - 1) return invalid(PEAR_TEXT, EPROTO);
    return pear_observed_text(value);
}

static pear_observation system_sysctl_integer(void *context, const char *name)
{
    (void)context;
    int value = 0;
    size_t size = sizeof(value);
    if (sysctlbyname(name, &value, &size, NULL, 0) != 0)
        return errno_result(PEAR_INTEGER, errno);
    if (size != sizeof(value)) return invalid(PEAR_INTEGER, EPROTO);
    return pear_observed_integer(value);
}

static pear_observation system_page_size(void *context)
{
    (void)context;
    errno = 0;
    long value = sysconf(_SC_PAGESIZE);
    if (value <= 0) return errno_result(PEAR_INTEGER, errno != 0 ? errno : EINVAL);
    return pear_observed_integer(value);
}

static pear_observation system_symbol(void *context, const char *name)
{
    (void)context;
    /* No resolved function is invoked. Lookup errors can contain private paths. */
    (void)dlerror();
    void *address = dlsym(RTLD_DEFAULT, name);
    const char *error = dlerror();
    return pear_observed_boolean(address != NULL && error == NULL);
}

static pear_observation signature_error(OSStatus status)
{
    if (status == errSecCSUnsigned) return pear_observed_text("unsigned");
    return pear_observation_error(PEAR_TEXT, PEAR_UNAVAILABLE,
                                  PEAR_ERROR_OSSTATUS, status);
}

static pear_observation system_signature(void *context)
{
    (void)context;
    SecCodeRef code = NULL;
    SecStaticCodeRef static_code = NULL;
    CFDictionaryRef information = NULL;
    OSStatus status = SecCodeCopySelf(kSecCSDefaultFlags, &code);
    if (status != errSecSuccess) return signature_error(status);
    status = SecCodeCopyStaticCode(code, kSecCSDefaultFlags, &static_code);
    CFRelease(code);
    if (status != errSecSuccess) return signature_error(status);
    /* Generic metadata suffices; do not request certificates or identity details. */
    status = SecCodeCopySigningInformation(static_code, kSecCSDefaultFlags, &information);
    CFRelease(static_code);
    if (status != errSecSuccess) return signature_error(status);
    if (information == NULL) return invalid(PEAR_TEXT, EPROTO);

    pear_observation result;
    CFTypeRef flags_object = CFDictionaryGetValue(information, kSecCodeInfoFlags);
    int64_t flags = 0;
    if (!CFDictionaryContainsKey(information, kSecCodeInfoIdentifier)) {
        result = pear_observed_text("unsigned");
    } else if (flags_object == NULL || CFGetTypeID(flags_object) != CFNumberGetTypeID() ||
               !CFNumberGetValue((CFNumberRef)flags_object, kCFNumberSInt64Type, &flags)) {
        result = invalid(PEAR_TEXT, EPROTO);
    } else {
        result = pear_observed_text((flags & kSecCodeSignatureAdhoc) ? "ad_hoc" : "signed");
    }
    CFRelease(information);
    return result;
}

const pear_source *pear_system_source(void)
{
    static const pear_source source = {
        NULL, system_architecture, system_sysctl_text, system_sysctl_integer,
        system_page_size, system_symbol, system_signature
    };
    return &source;
}

void pear_collect(const pear_source *source, pear_report *report)
{
    memset(report, 0, sizeof(*report));
    void *context = source != NULL ? source->context : NULL;
    report->architecture = checked(source != NULL && source->architecture != NULL
        ? source->architecture(context) : invalid(PEAR_TEXT, EINVAL), PEAR_TEXT);
    if (report->architecture.status == PEAR_OBSERVED &&
        strcmp(report->architecture.text, "arm64") != 0 &&
        strcmp(report->architecture.text, "arm64e") != 0 &&
        strcmp(report->architecture.text, "x86_64") != 0)
        report->architecture = pear_observation_error(PEAR_TEXT, PEAR_FAILED,
                                                       PEAR_ERROR_ERRNO, ENOTSUP);

    pear_observation translated = checked(source != NULL && source->sysctl_integer != NULL
        ? source->sysctl_integer(context, "sysctl.proc_translated")
        : invalid(PEAR_INTEGER, EINVAL), PEAR_INTEGER);
    translated.kind = PEAR_BOOLEAN;
    report->translated = checked(translated, PEAR_BOOLEAN);

    report->os_version = checked(source != NULL && source->sysctl_text != NULL
        ? source->sysctl_text(context, "kern.osproductversion")
        : invalid(PEAR_TEXT, EINVAL), PEAR_TEXT);
    report->os_build = checked(source != NULL && source->sysctl_text != NULL
        ? source->sysctl_text(context, "kern.osversion")
        : invalid(PEAR_TEXT, EINVAL), PEAR_TEXT);
    report->page_size_bytes = checked(source != NULL && source->page_size != NULL
        ? source->page_size(context) : invalid(PEAR_INTEGER, EINVAL), PEAR_INTEGER);
    if (report->page_size_bytes.status == PEAR_OBSERVED && report->page_size_bytes.number <= 0)
        report->page_size_bytes = invalid(PEAR_INTEGER, EPROTO);
    for (size_t i = 0; i < PEAR_SYMBOL_COUNT; ++i)
        report->symbols[i] = checked(source != NULL && source->symbol != NULL
            ? source->symbol(context, pear_symbol_names[i])
            : invalid(PEAR_BOOLEAN, EINVAL), PEAR_BOOLEAN);
    report->signature_category = checked(source != NULL && source->signature != NULL
        ? source->signature(context) : invalid(PEAR_TEXT, EINVAL), PEAR_TEXT);
    if (report->signature_category.status == PEAR_OBSERVED &&
        strcmp(report->signature_category.text, "unsigned") != 0 &&
        strcmp(report->signature_category.text, "ad_hoc") != 0 &&
        strcmp(report->signature_category.text, "signed") != 0)
        report->signature_category = invalid(PEAR_TEXT, EPROTO);
}

static void write_string(FILE *stream, const char *value)
{
    fputc('"', stream);
    for (size_t i = 0; i < PEAR_TEXT_CAPACITY && value[i] != '\0'; ++i) {
        unsigned char byte = (unsigned char)value[i];
        if (byte == '"' || byte == '\\') {
            fputc('\\', stream);
            fputc(byte, stream);
        } else if (byte < 0x20) {
            fprintf(stream, "\\u%04x", byte);
        } else fputc(byte, stream);
    }
    fputc('"', stream);
}

static void write_observation(FILE *stream, pear_observation value, pear_value_kind kind)
{
    value = checked(value, kind);
    const char *status = value.status == PEAR_OBSERVED ? "observed" :
                         value.status == PEAR_UNAVAILABLE ? "unavailable" : "failed";
    fprintf(stream, "{\"status\":\"%s\",\"value\":", status);
    if (value.status != PEAR_OBSERVED) fputs("null", stream);
    else if (kind == PEAR_TEXT) write_string(stream, value.text);
    else if (kind == PEAR_BOOLEAN) fputs(value.number ? "true" : "false", stream);
    else fprintf(stream, "%" PRId64, value.number);
    fputs(",\"error\":", stream);
    if (value.status == PEAR_OBSERVED) fputs("null", stream);
    else {
        const char *domain = value.error_domain == PEAR_ERROR_ERRNO ? "errno" :
                             value.error_domain == PEAR_ERROR_OSSTATUS ? "osstatus" : "internal";
        fprintf(stream, "{\"domain\":\"%s\",\"code\":%" PRId64 "}", domain, value.error_code);
    }
    fputc('}', stream);
}

int pear_write_json(FILE *stream, const pear_report *report)
{
    if (stream == NULL || report == NULL) { errno = EINVAL; return -1; }
    fputs("{\"schema_version\":1,\"probe_version\":\"" PEAR_PROBE_VERSION
          "\",\"scope\":\"current_process\",\"process\":{\"architecture\":", stream);
    write_observation(stream, report->architecture, PEAR_TEXT);
    fputs(",\"translated\":", stream);
    write_observation(stream, report->translated, PEAR_BOOLEAN);
    fputs("},\"host\":{\"os_version\":", stream);
    write_observation(stream, report->os_version, PEAR_TEXT);
    fputs(",\"os_build\":", stream);
    write_observation(stream, report->os_build, PEAR_TEXT);
    fputs(",\"page_size_bytes\":", stream);
    write_observation(stream, report->page_size_bytes, PEAR_INTEGER);
    fputs("},\"runtime_symbols\":{", stream);
    for (size_t i = 0; i < PEAR_SYMBOL_COUNT; ++i) {
        if (i != 0) fputc(',', stream);
        write_string(stream, pear_symbol_names[i]);
        fputc(':', stream);
        write_observation(stream, report->symbols[i], PEAR_BOOLEAN);
    }
    fputs("},\"signature\":{\"category\":", stream);
    write_observation(stream, report->signature_category, PEAR_TEXT);
    fputs(",\"validation\":\"not_assessed\",\"authorization\":\"not_assessed\"},"
          "\"capabilities\":{\"x18\":\"not_run\",\"page_4k\":\"not_run\","
          "\"memory_order\":\"not_run\",\"jit\":\"not_run\"},"
          "\"qualification\":{\"runtime\":\"not_assessed\","
          "\"rosetta_free_game\":\"not_assessed\",\"distribution\":\"not_assessed\"}}\n", stream);
    return ferror(stream) ? -1 : 0;
}
