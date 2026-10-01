/* Original Pear finite native PE-arena prerequisite fixture, MIT-licensed.
 * Geometry, region queries and fixed ARM64 instructions reuse Pear's retained
 * jit_layout_probe_v2.c and mapping_probe.c diagnostics. This is a standalone
 * single-threaded allocation/lifetime test, not Wine/FEX integration or a proof
 * against arbitrary dangling guest pointers. The supervisor validates actual
 * signing and provisioning before releasing the inherited control pipe.
 */
#include <errno.h>
#include <fcntl.h>
#include <libkern/OSCacheControl.h>
#include <libproc.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
#include <mach-o/loader.h>
#include <poll.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/sysctl.h>
#include <unistd.h>

#if !defined(__APPLE__) || !defined(__aarch64__)
#error Native ARM64 macOS is required.
#endif

#define PAGE_BYTES ((size_t)4096)
#define SLOT_BYTES ((size_t)65536)
#define SLOT_PAGES 16u
#define SLOT_COUNT 2u
#define INTERIOR_BYTES (SLOT_BYTES * SLOT_COUNT)
#define MAPPING_BYTES (INTERIOR_BYTES + SLOT_BYTES)
#define REUSE_ROUNDS 4u
#define MUTATOR_OFFSET 64u
#define SENTINEL_OFFSET 128u
#define BIT(page) (UINT32_C(1) << (page))
_Static_assert(MAPPING_BYTES == 196608, "one deterministic alignment block");
_Static_assert(SLOT_PAGES * PAGE_BYTES == SLOT_BYTES, "whole slots");

extern const struct mach_header_64 _mh_execute_header;
/* mov w0, #42/#84; ret */
static const uint32_t leaf42[] = {UINT32_C(0x52800540), UINT32_C(0xd65f03c0)};
static const uint32_t leaf84[] = {UINT32_C(0x52800a80), UINT32_C(0xd65f03c0)};
/* ldr w1,[x0]; add w1,w1,#1; str w1,[x0]; mov w0,w1; ret */
static const uint32_t increment[] = {
    UINT32_C(0xb9400001), UINT32_C(0x11000421), UINT32_C(0xb9000001),
    UINT32_C(0x2a0103e0), UINT32_C(0xd65f03c0)
};
extern const uint32_t pear_arena_increment_reference[];
extern void pear_arena_fault_write(volatile uint32_t *, uint32_t);
__asm__(".text\n.p2align 2\n.globl _pear_arena_increment_reference\n"
        ".private_extern _pear_arena_increment_reference\n_pear_arena_increment_reference:\n"
        "ldr w1, [x0]\nadd w1, w1, #1\nstr w1, [x0]\nmov w0, w1\nret\n"
        ".p2align 2\n.globl _pear_arena_fault_write\n"
        ".private_extern _pear_arena_fault_write\n_pear_arena_fault_write:\n"
        "str w1, [x0]\nret\n");

struct layout { const char *name; uint32_t code, data; unsigned int answer; };
static const struct layout layout_a = {"A", BIT(0) | BIT(2), BIT(1) | BIT(3), 42};
static const struct layout layout_b = {"B", BIT(0) | BIT(2) | BIT(4), BIT(1) | BIT(3) | BIT(5), 84};
/* This deliberately conflicts with page 1's permanently ordinary backing. */
static const struct layout layout_c = {"C", BIT(0) | BIT(1), BIT(3), 42};
enum state { RESERVED, PREPARING, PUBLISHED, FAILED, RETIRED };
static const char *const state_names[] = {"reserved", "preparing", "published", "failed", "retired"};
struct slot {
    unsigned char *base;
    enum state state;
    uint64_t generation;
    unsigned int references;
    uint32_t ordinary, ever_code;
    const struct layout *layout;
};
struct lease { unsigned int slot; uint64_t generation; int held; };
struct counts {
    unsigned int publications, preparation_failures, compatible_reuses, reuse_rounds;
    unsigned int leaf_calls, mutator_calls, ordinary_data_writes;
    unsigned int busy_retirement_rejections, exhaustion_rejections;
    unsigned int incompatible_reuse_rejections, stale_lease_rejections, retirements;
};
struct arena {
    unsigned char *mapping, *interior;
    struct slot slots[SLOT_COUNT];
    struct counts counts;
};
static const char *mode;
static const char *policy = "thread-jit";
static int page_wx;

static int published_code_protection(void)
{
    return page_wx ? PROT_READ | PROT_EXEC : PROT_READ | PROT_WRITE | PROT_EXEC;
}

static void emit(const char *event, const char *format, ...)
{
    va_list args;
    if (printf("{\"version\":1,\"record_kind\":\"pear_pe_arena_probe\","
               "\"mode\":\"%s\",\"policy\":\"%s\",\"event\":\"%s\",", mode, policy, event) < 0) _exit(90);
    va_start(args, format);
    int result = vprintf(format, args);
    va_end(args);
    if (result < 0 || puts("}") == EOF) _exit(90);
}

static int geometry(void)
{
    errno = 0;
    long user = sysconf(_SC_PAGESIZE);
    int user_error = user < 0 ? errno : 0;
    vm_size_t kernel = 0;
    mach_port_t host = mach_host_self();
    kern_return_t result = host_page_size(host, &kernel);
    kern_return_t released = mach_port_deallocate(mach_task_self(), host);
    int translated = -1;
    size_t size = sizeof(translated);
    int query = sysctlbyname("sysctl.proc_translated", &translated, &size, NULL, 0);
    int query_error = query ? errno : 0;
    int accepted = user == 4096 && vm_page_size == 4096 && kernel == 16384 &&
        result == KERN_SUCCESS && released == KERN_SUCCESS && !query && !user_error &&
        size == sizeof(translated) && translated == 0 && _mh_execute_header.cputype == CPU_TYPE_ARM64;
    emit("geometry", "\"user_page\":%ld,\"user_errno\":%d,\"vm_page\":%lu,"
         "\"kernel_page\":%lu,\"kernel_result\":%d,\"port_release_result\":%d,"
         "\"cpu_type\":%u,\"translation_query_result\":%d,\"translation_query_errno\":%d,"
         "\"translation_query_size\":%zu,\"translation_value\":%d,\"accepted\":%s",
         user, user_error, (unsigned long)vm_page_size, (unsigned long)kernel, result, released,
         (unsigned)_mh_execute_header.cputype, query, query_error, size, translated,
         accepted ? "true" : "false");
    return accepted ? 0 : -1;
}

static int handshake(void)
{
    const char *nonce = getenv("PEAR_ARENA_NONCE");
    const char *control = getenv("PEAR_ARENA_CONTROL_FD");
    if (!nonce || strlen(nonce) != 32 || !control || !*control) return -1;
    for (unsigned int i = 0; i < 32; ++i)
        if (!((nonce[i] >= '0' && nonce[i] <= '9') || (nonce[i] >= 'a' && nonce[i] <= 'f'))) return -1;
    for (const char *p = control; *p; ++p) if (*p < '0' || *p > '9') return -1;
    char *end = NULL;
    errno = 0;
    long parsed = strtol(control, &end, 10);
    if (errno || *end || parsed < 3 || parsed > 1048575) return -1;
    int fd = (int)parsed;
    struct stat info;
    if (fstat(fd, &info) || !S_ISFIFO(info.st_mode)) return -1;
    struct proc_bsdinfo identity = {0};
    int count = proc_pidinfo(getpid(), PROC_PIDTBSDINFO, 0, &identity, sizeof(identity));
    if (count != sizeof(identity) || identity.pbi_pid != (uint32_t)getpid() ||
        !identity.pbi_start_tvsec || identity.pbi_start_tvusec >= 1000000) { close(fd); return -1; }
    emit("identity", "\"pid\":%u,\"parent_pid\":%u,\"start_seconds\":%llu,"
         "\"start_microseconds\":%llu,\"nonce\":\"%s\"", identity.pbi_pid, identity.pbi_ppid,
         (unsigned long long)identity.pbi_start_tvsec, (unsigned long long)identity.pbi_start_tvusec, nonce);
    if (geometry()) { close(fd); return -1; }
    emit("ready", "\"nonce\":\"%s\",\"restricted_operations_started\":false,\"timeout_ms\":10000", nonce);
    struct pollfd pollfd = {.fd = fd, .events = POLLIN};
    int result = poll(&pollfd, 1, 10000);
    int error = result < 0 ? errno : 0;
    char token = 0;
    ssize_t got = result == 1 && (pollfd.revents & POLLIN) ? read(fd, &token, 1) : -1;
    int read_error = got < 0 && result == 1 ? errno : 0;
    int closed = close(fd);
    int close_error = closed ? errno : 0;
    int accepted = result == 1 && got == 1 && token == 'G' && !closed;
    emit("released", "\"poll_result\":%d,\"poll_errno\":%d,\"read_bytes\":%ld,"
         "\"read_errno\":%d,\"close_errno\":%d,\"accepted\":%s", result, error, (long)got,
         read_error, close_error, accepted ? "true" : "false");
    return accepted ? 0 : -1;
}

/* A containing VM entry may include adjacent pages with the same protection.
 * Require coverage of the complete requested page, never just its first byte. */
static int region(const char *phase, const void *pointer, size_t bytes, vm_prot_t protection, int exact)
{
    mach_vm_address_t address = (mach_vm_address_t)(uintptr_t)pointer, requested = address;
    mach_vm_size_t size = 0;
    vm_region_basic_info_data_64_t info = {0};
    mach_msg_type_number_t count = VM_REGION_BASIC_INFO_COUNT_64;
    mach_port_t object = MACH_PORT_NULL;
    kern_return_t result = mach_vm_region(mach_task_self(), &address, &size,
        VM_REGION_BASIC_INFO_64, (vm_region_info_t)&info, &count, &object);
    kern_return_t released = object == MACH_PORT_NULL ? KERN_SUCCESS : mach_port_deallocate(mach_task_self(), object);
    int covers = address <= requested && size >= requested - address && bytes <= size - (requested - address);
    int accepted = result == KERN_SUCCESS && count == VM_REGION_BASIC_INFO_COUNT_64 &&
        released == KERN_SUCCESS && covers && (!exact || (address == requested && size == bytes)) &&
        info.protection == protection && (info.max_protection & protection) == protection;
    if (!accepted || exact)
        emit("region", "\"phase\":\"%s\",\"mach_result\":%d,\"port_release_result\":%d,"
             "\"requested_bytes\":%zu,\"region_bytes\":%llu,\"covers_range\":%s,"
             "\"exact_required\":%s,\"current_protection\":%d,\"maximum_protection\":%d,"
             "\"expected_protection\":%d,\"accepted\":%s", phase, result, released, bytes,
             (unsigned long long)size, covers ? "true" : "false", exact ? "true" : "false",
             info.protection, info.max_protection, protection, accepted ? "true" : "false");
    return accepted ? 0 : -1;
}

static int protect_page(struct slot *slot, unsigned int index, unsigned int page, int protection)
{
    int result = mprotect(slot->base + page * PAGE_BYTES, PAGE_BYTES, protection);
    int error = result ? errno : 0;
    if (result)
        emit("protection_failure", "\"slot\":%u,\"generation\":%llu,\"page\":%u,"
             "\"state\":\"%s\",\"protection\":%d,\"result\":%d,\"errno\":%d", index,
             (unsigned long long)slot->generation, page, state_names[slot->state], protection, result, error);
    return result ? -1 : 0;
}

static int verify_slot(struct slot *slot, unsigned int index, int published)
{
    for (unsigned int page = 0; page < SLOT_PAGES; ++page)
    {
        int protection = PROT_NONE;
        if (published && (slot->layout->code & BIT(page))) protection = published_code_protection();
        else if (published && (slot->layout->data & BIT(page))) protection = PROT_READ | PROT_WRITE;
        if (region("slot_page", slot->base + page * PAGE_BYTES, PAGE_BYTES, protection, 0)) return -1;
    }
    emit("slot_protections", "\"slot\":%u,\"generation\":%llu,\"state\":\"%s\","
         "\"pages_checked\":16,\"published\":%s,\"code_mask\":%u,\"data_mask\":%u,"
         "\"ordinary_backing_mask\":%u,\"ever_code_mask\":%u,\"code_protection\":%d,\"accepted\":true", index,
         (unsigned long long)slot->generation, state_names[slot->state], published ? "true" : "false",
         published ? slot->layout->code : 0, published ? slot->layout->data : 0, slot->ordinary, slot->ever_code,
         published ? published_code_protection() : PROT_NONE);
    return 0;
}

static int make_inaccessible(struct slot *slot, unsigned int index)
{
    for (unsigned int page = 0; page < SLOT_PAGES; ++page)
        if (protect_page(slot, index, page, PROT_NONE)) return -1;
    return verify_slot(slot, index, 0);
}

static int initialize(struct arena *arena)
{
    int supported = pthread_jit_write_protect_supported_np();
    int reference = !memcmp(increment, pear_arena_increment_reference, sizeof(increment));
    emit("prerequisites", "\"jit_write_protection_supported\":%d,\"fixed_assembler_reference_matches\":%s",
         supported, reference ? "true" : "false");
    if (supported != 1 || !reference) return -1;
    int flags = MAP_PRIVATE | MAP_ANON | MAP_JIT;
    /* Reservation ordering follows QEMU tcg/region.c:611-625 at commit
     * 9638cb59ee3d3a505f4bb6b9a4bcc49c3df4edcc:
     * https://qemu.googlesource.com/qemu/+/9638cb59ee3d3a505f4bb6b9a4bcc49c3df4edcc/tcg/region.c
     * Start with NONE and promote only prepared code. This does not establish
     * that a published RWX page can later retire to NONE; the unchanged real
     * retirement, reuse and fault controls below still require that operation. */
    arena->mapping = mmap(NULL, MAPPING_BYTES, PROT_NONE, flags, -1, 0);
    int error = arena->mapping == MAP_FAILED ? errno : 0;
    emit("allocation", "\"requested_bytes\":%zu,\"jit_mapping_attempts\":1,\"flags\":%d,\"initial_protection\":0,"
         "\"result\":%d,\"errno\":%d", MAPPING_BYTES, flags, arena->mapping == MAP_FAILED ? -1 : 0, error);
    if (arena->mapping == MAP_FAILED) { arena->mapping = NULL; return -1; }
    uintptr_t base = (uintptr_t)arena->mapping;
    size_t prefix = (SLOT_BYTES - (base & (SLOT_BYTES - 1))) & (SLOT_BYTES - 1);
    int extent = base <= UINTPTR_MAX - MAPPING_BYTES;
    int fit = prefix < SLOT_BYTES && prefix <= MAPPING_BYTES && INTERIOR_BYTES <= MAPPING_BYTES - prefix;
    int aligned = !(base & (PAGE_BYTES - 1)) && extent && !((base + prefix) & (SLOT_BYTES - 1));
    emit("alignment", "\"prefix_bytes\":%zu,\"interior_bytes\":%zu,\"interior_alignment\":65536,"
         "\"mapping_extent_fits\":%s,\"interior_fits\":%s,\"aligned\":%s,\"allocation_attempts\":1",
         prefix, INTERIOR_BYTES, extent ? "true" : "false", fit ? "true" : "false", aligned ? "true" : "false");
    if (!extent || !fit || !aligned || region("allocation", arena->mapping, MAPPING_BYTES, VM_PROT_NONE, 1)) return -1;
    arena->interior = arena->mapping + prefix;
    for (unsigned int index = 0; index < SLOT_COUNT; ++index)
    {
        arena->slots[index].base = arena->interior + index * SLOT_BYTES;
        arena->slots[index].state = RESERVED;
        if (make_inaccessible(&arena->slots[index], index)) return -1;
    }
    return 0;
}

static int compatible(const struct slot *slot, const struct layout *layout)
{
    uint32_t valid = (UINT32_C(1) << SLOT_PAGES) - 1;
    return layout && !(layout->code & layout->data) && !((layout->code | layout->data) & ~valid) &&
        !(layout->code & slot->ordinary) && !(layout->data & slot->ever_code);
}

/* Both real preparation and the capacity control submit an allocation request
 * here. A rejected admission cannot change a slot or create another mapping. */
struct admission { unsigned int index; int reused; };
enum admission_result { ADMITTED, CAPACITY_EXHAUSTED, INCOMPATIBLE_LAYOUT, INVALID_REQUEST };
static enum admission_result admit(struct arena *arena, int preferred, const struct layout *layout,
                                   struct admission *admission)
{
    if (preferred < -1 || preferred >= (int)SLOT_COUNT || !layout) return INVALID_REQUEST;
    unsigned int available = 0;
    for (unsigned int index = 0; index < SLOT_COUNT; ++index)
    {
        if (preferred >= 0 && index != (unsigned int)preferred) continue;
        struct slot *slot = &arena->slots[index];
        if (slot->state != RESERVED && slot->state != RETIRED) continue;
        ++available;
        if (!compatible(slot, layout)) continue;
        if (slot->references || slot->generation == UINT64_MAX) return INVALID_REQUEST;
        *admission = (struct admission){index, slot->state == RETIRED};
        slot->state = PREPARING;
        ++slot->generation;
        slot->layout = layout;
        return ADMITTED;
    }
    return available ? INCOMPATIBLE_LAYOUT : CAPACITY_EXHAUSTED;
}

/* Ordinary pages are a one-way conversion of previously uncommitted JIT
 * backing. Once assigned, neither ordinary backing nor published code backing
 * may change class; compatible layouts may only leave such pages unused. */
static int prepare(struct arena *arena, unsigned int index, const struct layout *layout, int inject_failure)
{
    struct admission admission = {0};
    if (admit(arena, (int)index, layout, &admission) != ADMITTED || admission.index != index) return -1;
    struct slot *slot = &arena->slots[index];
    int reused = admission.reused;
    emit("preparation", "\"slot\":%u,\"generation\":%llu,\"layout\":\"%s\","
         "\"reused_slot\":%s,\"inject_failure\":%s", index, (unsigned long long)slot->generation,
         layout->name, reused ? "true" : "false", inject_failure ? "true" : "false");
    unsigned int new_holes = 0;
    for (unsigned int page = 0; page < SLOT_PAGES; ++page)
    {
        if (!(layout->data & BIT(page))) continue;
        if (!(slot->ordinary & BIT(page)))
        {
            void *target = slot->base + page * PAGE_BYTES;
            void *actual = mmap(target, PAGE_BYTES, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANON | MAP_FIXED, -1, 0);
            int error = actual == MAP_FAILED ? errno : 0;
            emit("data_hole", "\"slot\":%u,\"generation\":%llu,\"page\":%u,\"bytes\":4096,"
                 "\"map_jit\":false,\"exact_owned_subrange\":%s,\"result\":%d,\"errno\":%d", index,
                 (unsigned long long)slot->generation, page, actual == target ? "true" : "false",
                 actual == MAP_FAILED ? -1 : 0, error);
            if (actual != target) return -1;
            slot->ordinary |= BIT(page);
            ++new_holes;
        }
        else if (protect_page(slot, index, page, PROT_READ | PROT_WRITE)) return -1;
        if (region("ordinary_4k", slot->base + page * PAGE_BYTES, PAGE_BYTES, VM_PROT_READ | VM_PROT_WRITE, 1)) return -1;
        memset(slot->base + page * PAGE_BYTES, 0, PAGE_BYTES);
        if (inject_failure && new_holes == 1)
        {
            slot->state = FAILED;
            ++arena->counts.preparation_failures;
            emit("injected_preparation_failure", "\"slot\":%u,\"generation\":%llu,"
                 "\"new_holes\":1,\"ordinary_backing_mask\":%u,\"code_published\":false", index,
                 (unsigned long long)slot->generation, slot->ordinary);
            if (make_inaccessible(slot, index)) return -1;
            slot->state = RETIRED;
            emit("rollback", "\"slot\":%u,\"generation\":%llu,\"backing_retained\":true,"
                 "\"all_pages_inaccessible\":true,\"reusable\":true", index, (unsigned long long)slot->generation);
            return 1;
        }
    }
    /* Compare the existing per-thread policy with the public mprotect W^X
     * path for MAP_JIT entries that never become RWX. This policy selection is
     * diagnostic only. It does not select a Wine runtime memory policy.
     * Apple vm_map.c retains non-RWX JIT entries on macOS; RWX promotion can
     * make a later protection downgrade unavailable on the running platform.
     */
    int write_protection = page_wx ? PROT_READ | PROT_WRITE : published_code_protection();
    unsigned int pages_checked = 0;
    for (unsigned int page = 0; page < SLOT_PAGES; ++page)
    {
        if (!(layout->code & BIT(page))) continue;
        if (protect_page(slot, index, page, write_protection) ||
            region("code_write_page", slot->base + page * PAGE_BYTES, PAGE_BYTES, write_protection, 0)) return -1;
        ++pages_checked;
    }
    emit("code_write_ready", "\"slot\":%u,\"generation\":%llu,\"layout\":\"%s\","
         "\"code_mask\":%u,\"code_protection\":%d,\"pages_checked\":%u,\"accepted\":true", index,
         (unsigned long long)slot->generation, layout->name, layout->code, write_protection, pages_checked);
    /* All bounds/classes and OS permissions are validated before opening this
     * native writer window. No guest call, logger, allocator or non-local exit.
     * Page W^X never uses the thread JIT toggle or requests RWX protection. */
    if (!page_wx) pthread_jit_write_protect_np(0);
    for (unsigned int page = 0; page < SLOT_PAGES; ++page)
    {
        if (!(layout->code & BIT(page))) continue;
        memset(slot->base + page * PAGE_BYTES, 0, PAGE_BYTES);
        memcpy(slot->base + page * PAGE_BYTES, layout->answer == 42 ? leaf42 : leaf84, sizeof(leaf42));
    }
    memcpy(slot->base + MUTATOR_OFFSET, increment, sizeof(increment));
    if (!page_wx) pthread_jit_write_protect_np(1);
    for (unsigned int page = 0; page < SLOT_PAGES; ++page)
    {
        if (!(layout->code & BIT(page))) continue;
        if (page_wx && protect_page(slot, index, page, PROT_READ | PROT_EXEC)) return -1;
        sys_icache_invalidate(slot->base + page * PAGE_BYTES, PAGE_BYTES);
    }
    slot->ever_code |= layout->code;
    slot->state = PUBLISHED;
    ++arena->counts.publications;
    if (reused) ++arena->counts.compatible_reuses;
    for (unsigned int page = 0; page < SLOT_PAGES; ++page)
        if (layout->data & BIT(page))
            *(volatile uint32_t *)(slot->base + page * PAGE_BYTES + SENTINEL_OFFSET) =
                UINT32_C(0x13570000) + 256 * index + (uint32_t)slot->generation;
    if (verify_slot(slot, index, 1)) return -1;
    emit("publication", "\"slot\":%u,\"generation\":%llu,\"layout\":\"%s\","
         "\"native_writer_closed\":true,\"cache_invalidated\":true,\"code_mask\":%u,"
         "\"data_mask\":%u,\"ordinary_backing_mask\":%u,\"ever_code_mask\":%u,"
         "\"code_protection\":%d,\"pthread_jit_toggle_used\":%s", index,
         (unsigned long long)slot->generation, layout->name, layout->code, layout->data,
         slot->ordinary, slot->ever_code, published_code_protection(), page_wx ? "false" : "true");
    return 0;
}

static int enter(struct arena *arena, unsigned int index, uint64_t generation, struct lease *lease)
{
    struct slot *slot = &arena->slots[index];
    if (lease->held || slot->state != PUBLISHED || generation != slot->generation || slot->references == UINT32_MAX) return -1;
    ++slot->references;
    *lease = (struct lease){index, generation, 1};
    return 0;
}

static int leave(struct arena *arena, struct lease *lease)
{
    if (!lease->held || lease->slot >= SLOT_COUNT) return -1;
    struct slot *slot = &arena->slots[lease->slot];
    if (slot->generation != lease->generation || !slot->references) return -1;
    --slot->references;
    lease->held = 0;
    return 0;
}

static int retire(struct arena *arena, unsigned int index)
{
    struct slot *slot = &arena->slots[index];
    if (slot->state != PUBLISHED) return -1;
    if (slot->references)
    {
        ++arena->counts.busy_retirement_rejections;
        emit("retirement_rejected", "\"slot\":%u,\"generation\":%llu,\"reason\":\"active_lease\","
             "\"active_leases\":%u,\"published_preserved\":true", index,
             (unsigned long long)slot->generation, slot->references);
        return 1;
    }
    if (make_inaccessible(slot, index)) return -1;
    slot->state = RETIRED;
    ++arena->counts.retirements;
    emit("retirement", "\"slot\":%u,\"generation\":%llu,\"active_leases\":0,"
         "\"all_pages_inaccessible\":true,\"backing_retained\":true,\"reusable\":true",
         index, (unsigned long long)slot->generation);
    return 0;
}

static int exercise(struct arena *arena, unsigned int index)
{
    struct slot *slot = &arena->slots[index];
    struct lease lease = {0};
    if (enter(arena, index, slot->generation, &lease) || retire(arena, index) != 1 || slot->state != PUBLISHED) return -1;
    for (unsigned int page = 0; page < SLOT_PAGES; ++page)
    {
        if (slot->layout->code & BIT(page))
        {
            void *code = slot->base + page * PAGE_BYTES;
            const uint32_t *expected = slot->layout->answer == 42 ? leaf42 : leaf84;
            if (memcmp(code, expected, sizeof(leaf42))) return -1;
            unsigned int (*volatile leaf)(void) = (unsigned int (*)(void))code;
            unsigned int answer = leaf();
            ++arena->counts.leaf_calls;
            emit("leaf_return", "\"slot\":%u,\"generation\":%llu,\"page\":%u,\"value\":%u,"
                 "\"expected\":%u,\"matched\":%s", index, (unsigned long long)slot->generation,
                 page, answer, slot->layout->answer, answer == slot->layout->answer ? "true" : "false");
            if (answer != slot->layout->answer) return -1;
        }
        if (slot->layout->data & BIT(page))
        {
            volatile uint32_t *word = (volatile uint32_t *)(slot->base + page * PAGE_BYTES);
            volatile uint32_t *sentinel = (volatile uint32_t *)(slot->base + page * PAGE_BYTES + SENTINEL_OFFSET);
            uint32_t expected_sentinel = UINT32_C(0x13570000) + 256 * index + (uint32_t)slot->generation;
            if (*sentinel != expected_sentinel || memcmp(slot->base + MUTATOR_OFFSET, increment, sizeof(increment))) return -1;
            uint32_t expected = 100 * index + 10 * (uint32_t)slot->generation + page;
            *word = expected;
            ++arena->counts.ordinary_data_writes;
            uint32_t (*volatile mutator)(volatile uint32_t *) =
                (uint32_t (*)(volatile uint32_t *))(slot->base + MUTATOR_OFFSET);
            uint32_t answer = mutator(word);
            ++arena->counts.mutator_calls;
            int matched = answer == expected + 1 && *word == answer && *sentinel == expected_sentinel;
            emit("mutator_return", "\"slot\":%u,\"generation\":%llu,\"page\":%u,\"value\":%u,"
                 "\"data_value\":%u,\"expected\":%u,\"sentinel_preserved\":%s,\"matched\":%s",
                 index, (unsigned long long)slot->generation, page, answer, *word, expected + 1,
                 *sentinel == expected_sentinel ? "true" : "false", matched ? "true" : "false");
            if (!matched) return -1;
        }
    }
    return leave(arena, &lease);
}

static int reject_exhaustion(struct arena *arena)
{
    struct slot before[SLOT_COUNT];
    memcpy(before, arena->slots, sizeof(before));
    struct admission admission = {0};
    enum admission_result result = admit(arena, -1, &layout_a, &admission);
    if (result != CAPACITY_EXHAUSTED) return -1;
    for (unsigned int index = 0; index < SLOT_COUNT; ++index)
    {
        const struct slot *old = &before[index], *now = &arena->slots[index];
        if (old->base != now->base || old->state != now->state || old->generation != now->generation ||
            old->references != now->references || old->ordinary != now->ordinary ||
            old->ever_code != now->ever_code || old->layout != now->layout) return -1;
        if (verify_slot(&arena->slots[index], index, 1)) return -1;
    }
    ++arena->counts.exhaustion_rejections;
    emit("allocation_rejected", "\"reason\":\"slot_capacity\",\"capacity\":2,\"available\":0,"
         "\"request_submitted\":true,\"admission_result\":%d,\"additional_mapping_attempts\":0,"
         "\"published_slots_preserved\":true,\"slot_metadata_preserved\":true", result);
    return 0;
}

static int reject_stale(struct arena *arena, uint64_t generation)
{
    struct lease stale = {0};
    if (!enter(arena, 0, generation, &stale) || stale.held) return -1;
    ++arena->counts.stale_lease_rejections;
    emit("lease_rejected", "\"slot\":0,\"requested_generation\":%llu,\"current_generation\":%llu,"
         "\"state\":\"%s\",\"active_leases\":%u", (unsigned long long)generation,
         (unsigned long long)arena->slots[0].generation, state_names[arena->slots[0].state], arena->slots[0].references);
    return 0;
}

static int lifecycle(struct arena *arena)
{
    if (prepare(arena, 0, &layout_a, 1) != 1 || arena->slots[0].ordinary != BIT(1) ||
        prepare(arena, 0, &layout_a, 0) || prepare(arena, 1, &layout_a, 0) ||
        exercise(arena, 0) || exercise(arena, 1) || reject_exhaustion(arena)) return -1;
    uint64_t old_generation = arena->slots[0].generation;
    unsigned char *same_address = arena->slots[0].base;
    if (retire(arena, 0) || reject_stale(arena, old_generation)) return -1;
    uint32_t old_backing = arena->slots[0].ordinary;
    if (compatible(&arena->slots[0], &layout_c) || prepare(arena, 0, &layout_c, 0) != -1 ||
        arena->slots[0].state != RETIRED || arena->slots[0].generation != old_generation ||
        arena->slots[0].ordinary != old_backing || verify_slot(&arena->slots[0], 0, 0)) return -1;
    ++arena->counts.incompatible_reuse_rejections;
    emit("reuse_rejected", "\"slot\":0,\"layout\":\"C\",\"reason\":\"ordinary_page_requested_as_code\","
         "\"page\":1,\"generation_preserved\":true,\"backing_preserved\":true,\"permissions_preserved\":true");
    for (unsigned int round = 0; round < REUSE_ROUNDS; ++round)
    {
        const struct layout *layout = round % 2 ? &layout_a : &layout_b;
        uint64_t before = arena->slots[0].generation;
        if (prepare(arena, 0, layout, 0) || arena->slots[0].base != same_address ||
            arena->slots[0].generation != before + 1 || exercise(arena, 0) || exercise(arena, 1) ||
            reject_exhaustion(arena) || (!round && reject_stale(arena, old_generation))) return -1;
        ++arena->counts.reuse_rounds;
        emit("reuse", "\"round\":%u,\"slot\":0,\"layout\":\"%s\",\"generation\":%llu,"
             "\"same_owned_address\":true,\"peer_generation_preserved\":%s,\"remaining_jit_backing_preserved\":true",
             round, layout->name, (unsigned long long)arena->slots[0].generation,
             arena->slots[1].generation == 1 ? "true" : "false");
        if (round + 1 < REUSE_ROUNDS && retire(arena, 0)) return -1;
    }
    struct counts *c = &arena->counts;
    int matched = c->publications == 6 && c->preparation_failures == 1 && c->compatible_reuses == 5 &&
        c->reuse_rounds == 4 && c->leaf_calls == 22 && c->mutator_calls == 22 && c->ordinary_data_writes == 22 &&
        c->busy_retirement_rejections == 10 && c->exhaustion_rejections == 5 &&
        c->incompatible_reuse_rejections == 1 && c->stale_lease_rejections == 2 && c->retirements == 4 &&
        arena->slots[0].generation == 6 && arena->slots[1].generation == 1 &&
        arena->slots[0].state == PUBLISHED && arena->slots[1].state == PUBLISHED &&
        !arena->slots[0].references && !arena->slots[1].references &&
        arena->slots[0].ordinary == (BIT(1) | BIT(3) | BIT(5)) && arena->slots[1].ordinary == (BIT(1) | BIT(3)) &&
        arena->slots[0].ever_code == (BIT(0) | BIT(2) | BIT(4));
    emit("lifecycle_summary", "\"passed\":%s,\"publications\":%u,\"preparation_failures\":%u,"
         "\"compatible_reuses\":%u,\"reuse_rounds\":%u,\"leaf_calls\":%u,\"mutator_calls\":%u,"
         "\"ordinary_data_writes\":%u,\"busy_retirement_rejections\":%u,\"exhaustion_rejections\":%u,"
         "\"incompatible_reuse_rejections\":%u,\"stale_lease_rejections\":%u,\"retirements\":%u,"
         "\"slot0_generation\":%llu,\"slot1_generation\":%llu,\"active_leases\":%u,\"published_slots\":2,"
         "\"slot0_ordinary_mask\":%u,\"slot1_ordinary_mask\":%u,\"retained_unused_ordinary_pages\":1,"
         "\"jit_mapping_attempts\":1,\"diagnostic_only\":true,\"runtime_qualified\":false", matched ? "true" : "false",
         c->publications, c->preparation_failures, c->compatible_reuses, c->reuse_rounds, c->leaf_calls,
         c->mutator_calls, c->ordinary_data_writes, c->busy_retirement_rejections, c->exhaustion_rejections,
         c->incompatible_reuse_rejections, c->stale_lease_rejections, c->retirements,
         (unsigned long long)arena->slots[0].generation, (unsigned long long)arena->slots[1].generation,
         arena->slots[0].references + arena->slots[1].references, arena->slots[0].ordinary, arena->slots[1].ordinary);
    return matched ? 0 : -1;
}

static int fault_control(struct arena *arena)
{
    struct slot *slot = &arena->slots[0];
    unsigned char *target = slot->base;
    uintptr_t pc = (uintptr_t)target;
    const char *access = "execute";
    if (!strcmp(mode, "retired-call"))
    {
        if (retire(arena, 0)) return -1;
    }
    else if (!strcmp(mode, "data-exec"))
    {
        target += PAGE_BYTES;
        memcpy(target, leaf42, sizeof(leaf42));
        sys_icache_invalidate(target, sizeof(leaf42));
        if (region("data_exec_target", target, PAGE_BYTES, VM_PROT_READ | VM_PROT_WRITE, 1)) return -1;
        pc = (uintptr_t)target;
    }
    else if (!strcmp(mode, "protected-write"))
    {
        pc = (uintptr_t)pear_arena_fault_write;
        access = "write";
    }
    else if (!strcmp(mode, "preparation-exec"))
    {
        if (!page_wx || retire(arena, 0)) return -1;
        struct admission admission = {0};
        if (admit(arena, 0, &layout_a, &admission) != ADMITTED || admission.index != 0 ||
            !admission.reused || slot->generation != 7 || slot->state != PREPARING) return -1;
        emit("preparation", "\"slot\":0,\"generation\":%llu,\"layout\":\"A\","
             "\"reused_slot\":true,\"inject_failure\":false", (unsigned long long)slot->generation);
        /* Leave the attempted instruction in an actually writable, non-executable
         * preparation page. All its other pages remain inaccessible. The peer's
         * published RX code must still execute before this control is armed. */
        if (protect_page(slot, 0, 0, PROT_READ | PROT_WRITE)) return -1;
        memcpy(target, leaf42, sizeof(leaf42));
        sys_icache_invalidate(target, sizeof(leaf42));
        if (memcmp(target, leaf42, sizeof(leaf42))) return -1;
        for (unsigned int page = 0; page < SLOT_PAGES; ++page)
            if (region("preparation_fault_page", slot->base + page * PAGE_BYTES, PAGE_BYTES,
                       page == 0 ? VM_PROT_READ | VM_PROT_WRITE : VM_PROT_NONE, 0)) return -1;
        struct slot *peer = &arena->slots[1];
        struct lease lease = {0};
        if (peer->generation != 1 || peer->layout != &layout_a || verify_slot(peer, 1, 1) ||
            enter(arena, 1, peer->generation, &lease) || memcmp(peer->base, leaf42, sizeof(leaf42))) return -1;
        unsigned int (*volatile peer_leaf)(void) = (unsigned int (*)(void))peer->base;
        unsigned int answer = peer_leaf();
        if (leave(arena, &lease)) return -1;
        emit("preparation_fault_ready", "\"slot\":0,\"generation\":%llu,\"state\":\"preparing\","
             "\"target_page\":0,\"target_protection\":3,\"target_pages_checked\":16,"
             "\"peer_slot\":1,\"peer_generation\":1,\"peer_pages_checked\":16,\"peer_leaf_value\":%u,"
             "\"peer_leaf_expected\":42,\"peer_leaf_matched\":%s,\"peer_lease_released\":true,"
             "\"published\":false,\"accepted\":%s", (unsigned long long)slot->generation, answer,
             answer == 42 ? "true" : "false", answer == 42 ? "true" : "false");
        if (answer != 42) return -1;
    }
    else if (strcmp(mode, "writer-exec") || page_wx) return -1;
    /* Raw addresses are private diagnostic evidence for the external crash
     * matcher, never public support metadata. Only the exact armed operation
     * below can satisfy the paired negative control. */
    emit("fault_armed", "\"control\":\"%s\",\"slot\":0,\"generation\":%llu,\"state\":\"%s\","
         "\"access\":\"%s\",\"expected_pc_min\":%llu,\"expected_pc_max\":%llu,"
         "\"expected_address_min\":%llu,\"expected_address_max\":%llu,"
         "\"lifecycle_passed\":true,\"writer_mode_requested_next\":%s,\"expected_outcome\":\"os_fault\"",
         mode, (unsigned long long)slot->generation, state_names[slot->state], access,
         (unsigned long long)pc, (unsigned long long)(pc + 4), (unsigned long long)(uintptr_t)target,
         (unsigned long long)((uintptr_t)target + 4), !strcmp(mode, "writer-exec") ? "true" : "false");
    if (!strcmp(mode, "protected-write")) pear_arena_fault_write((volatile uint32_t *)target, leaf84[0]);
    else
    {
        unsigned int (*volatile leaf)(void) = (unsigned int (*)(void))target;
        if (!strcmp(mode, "writer-exec")) pthread_jit_write_protect_np(0);
        unsigned int answer = leaf();
        if (!strcmp(mode, "writer-exec")) pthread_jit_write_protect_np(1);
        emit("unexpected_fault_return", "\"value\":%u", answer);
    }
    emit("fault_not_delivered", "\"unexpected\":true");
    return 1;
}

int main(int argc, char **argv)
{
    if (setvbuf(stdout, NULL, _IONBF, 0) || setvbuf(stderr, NULL, _IONBF, 0)) return 90;
    if (argc != 2 && argc != 3) return 64;
    if (argc == 3) policy = argv[2];
    if (strcmp(policy, "thread-jit") && strcmp(policy, "page-wx")) return 64;
    page_wx = !strcmp(policy, "page-wx");
    mode = argv[1];
    if (strcmp(mode, "lifecycle") && strcmp(mode, "protected-write") &&
        strcmp(mode, "retired-call") && strcmp(mode, "data-exec") &&
        strcmp(mode, page_wx ? "preparation-exec" : "writer-exec")) return 64;
    emit("begin", "\"diagnostic_only\":true,\"runtime_qualified\":false,\"single_threaded\":true,"
         "\"mapping_bytes\":196608,\"interior_bytes\":131072,\"slot_bytes\":65536,"
         "\"slot_capacity\":2,\"guest_page_bytes\":4096,\"reuse_rounds\":4,\"private_vm_flags\":false");
    if (handshake()) return 65;
    struct arena arena = {0};
    int exit_code = 0;
    if (initialize(&arena)) { exit_code = 66; goto cleanup; }
    if (lifecycle(&arena)) { exit_code = 67; goto cleanup; }
    if (strcmp(mode, "lifecycle"))
    {
        int result = fault_control(&arena);
        exit_code = result < 0 ? 68 : 79;
        goto cleanup;
    }
    if (retire(&arena, 0) || retire(&arena, 1)) { exit_code = 69; goto cleanup; }
    emit("all_retired", "\"slots\":2,\"active_leases\":0,\"retirements\":%u,"
         "\"backing_retained_until_final_unmap\":true", arena.counts.retirements);
cleanup:
    if (arena.mapping)
    {
        int result = munmap(arena.mapping, MAPPING_BYTES);
        int error = result ? errno : 0;
        emit("cleanup", "\"original_mapping_bytes\":196608,\"result\":%d,\"errno\":%d,"
             "\"prior_exit_code\":%d", result, error, exit_code);
        if (result && !exit_code) exit_code = 70;
    }
    emit("result", "\"exit_code\":%d,\"passed\":%s,\"diagnostic_only\":true,\"runtime_qualified\":false",
         exit_code, exit_code == 0 ? "true" : "false");
    return exit_code;
}
