#include "observations.h"

#include <errno.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>

/* Only this test executable accepts fixture names; the shipped CLI does not. */
typedef struct {
    const char *name;
} fixture_context;

static bool is_case(void *context, const char *name)
{
    const fixture_context *fixture = context;
    return strcmp(fixture->name, name) == 0;
}

static pear_observation architecture(void *context)
{
    if (is_case(context, "unsupported-architecture"))
        return pear_observed_text("fixture-unsupported-architecture");
    if (is_case(context, "intel-architecture"))
        return pear_observed_text("x86_64");
    return pear_observed_text("arm64");
}

static pear_observation sysctl_text(void *context, const char *name)
{
    if (strcmp(name, "kern.osversion") == 0)
        return pear_observed_text("fixture-build");
    if (strcmp(name, "kern.osproductversion") != 0)
        return pear_observation_error(PEAR_TEXT, PEAR_UNAVAILABLE,
                                      PEAR_ERROR_ERRNO, ENOENT);

    if (is_case(context, "adversarial-text")) {
        char text[PEAR_TEXT_CAPACITY];
        const char suffix[] =
            " quote:\" slash:/ backslash:\\ fake:\"forged\":true UTF-8:\xe2\x98\x83";
        size_t offset = 0;
        for (int value = 1; value <= 31; ++value)
            text[offset++] = (char)value;
        memcpy(text + offset, suffix, sizeof(suffix));
        return pear_observed_text(text);
    }
    if (is_case(context, "oversized-text")) {
        char text[PEAR_TEXT_CAPACITY + 1];
        memset(text, 'x', sizeof(text) - 1);
        text[sizeof(text) - 1] = '\0';
        return pear_observed_text(text);
    }
    if (is_case(context, "invalid-utf8"))
        return pear_observed_text("invalid:\xff");
    return pear_observed_text("fixture-os-version");
}

static pear_observation sysctl_integer(void *context, const char *name)
{
    if (strcmp(name, "sysctl.proc_translated") != 0)
        return pear_observation_error(PEAR_INTEGER, PEAR_UNAVAILABLE,
                                      PEAR_ERROR_ERRNO, ENOENT);
    if (is_case(context, "translation-denied"))
        return pear_observation_error(PEAR_INTEGER, PEAR_UNAVAILABLE,
                                      PEAR_ERROR_ERRNO, EPERM);
    if (is_case(context, "translation-missing"))
        return pear_observation_error(PEAR_INTEGER, PEAR_UNAVAILABLE,
                                      PEAR_ERROR_ERRNO, ENOENT);
    if (is_case(context, "translation-unexpected"))
        return pear_observed_integer(2);
    if (is_case(context, "translation-observed"))
        return pear_observed_integer(1);
    return pear_observed_integer(0);
}

static pear_observation page_size(void *context)
{
    (void)context;
    return pear_observed_integer(16384);
}

static pear_observation symbol(void *context, const char *name)
{
    (void)name;
    return pear_observed_boolean(!is_case(context, "missing-symbols"));
}

static pear_observation signature(void *context)
{
    if (is_case(context, "unavailable-signature"))
        return pear_observation_error(PEAR_TEXT, PEAR_UNAVAILABLE,
                                      PEAR_ERROR_OSSTATUS, -12345);
    return pear_observed_text("ad_hoc");
}

int main(int argc, char **argv)
{
    static const char *const cases[] = {
        "baseline", "translation-denied", "translation-missing",
        "translation-unexpected", "translation-observed", "missing-symbols",
        "unavailable-signature", "unsupported-architecture",
        "intel-architecture", "adversarial-text", "oversized-text", "invalid-utf8"
    };
    bool known = false;
    if (argc == 2) {
        for (size_t i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i)
            known = known || strcmp(argv[1], cases[i]) == 0;
    }
    if (!known) {
        fputs("A known diagnostic fixture name is required.\n", stderr);
        return 2;
    }

    fixture_context context = { .name = argv[1] };
    const pear_source source = {
        .context = &context,
        .architecture = architecture,
        .sysctl_text = sysctl_text,
        .sysctl_integer = sysctl_integer,
        .page_size = page_size,
        .symbol = symbol,
        .signature = signature
    };
    pear_report report;
    pear_collect(&source, &report);
    return pear_write_json(stdout, &report) == 0 ? 0 : 1;
}
