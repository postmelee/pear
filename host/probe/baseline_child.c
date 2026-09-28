#include "baseline.h"

#include <errno.h>
#include <libkern/OSCacheControl.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
#include <pthread.h>
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <unistd.h>

#if !defined(__aarch64__) && !defined(__arm64__)
#error "The baseline child must be built for ARM64."
#endif

/* Semantic failures use the internal domain, never an invented OS error. */
enum {
    READBACK_MISMATCH = 1,
    PROTECTED_WRITE_SUCCEEDED,
    JIT_PROTECTION_UNSUPPORTED,
    LOW_ADDRESS_MISMATCH,
    JIT_RETURN_MISMATCH
};

static void record_step(pear_baseline_packet *packet, size_t index,
                        pear_step_status status, pear_baseline_domain domain,
                        int64_t error, int64_t value) {
    packet->steps[index].status = status;
    packet->steps[index].error_domain = domain;
    packet->steps[index].error_code = error;
    packet->steps[index].value = value;
}

static void passed(pear_baseline_packet *packet, size_t index, int64_t value) {
    record_step(packet, index, PEAR_STEP_PASSED, PEAR_DOMAIN_NONE, 0, value);
}

static void errno_failure(pear_baseline_packet *packet, size_t index, int error) {
    record_step(packet, index, PEAR_STEP_FAILED, PEAR_DOMAIN_ERRNO, error, 0);
}

static void internal_failure(pear_baseline_packet *packet, size_t index,
                             int code, int64_t value) {
    record_step(packet, index, PEAR_STEP_FAILED, PEAR_DOMAIN_INTERNAL, code, value);
}

static int emit_packet(const pear_baseline_packet *packet) {
    const unsigned char *bytes = (const unsigned char *)packet;
    size_t remaining = sizeof(*packet);
    while (remaining > 0) {
        ssize_t amount = write(STDOUT_FILENO, bytes, remaining);
        if (amount < 0 && errno == EINTR) continue;
        if (amount <= 0) return -1;
        bytes += (size_t)amount;
        remaining -= (size_t)amount;
    }
    return 0;
}

static void release_mapping(pear_baseline_packet *packet, size_t index,
                            void *mapping, size_t size) {
    if (munmap(mapping, size) == 0) passed(packet, index, 0);
    else errno_failure(packet, index, errno);
}

static bool write_and_read(pear_baseline_packet *packet, size_t index,
                           volatile uint32_t *memory, uint32_t expected) {
    *memory = expected;
    uint32_t observed = *memory;
    if (observed == expected) {
        passed(packet, index, observed);
        return true;
    }
    internal_failure(packet, index, READBACK_MISMATCH, observed);
    return false;
}

static int memory_probe(pear_baseline_packet *packet, size_t size, bool fault) {
    void *mapping = mmap(NULL, size, PROT_READ | PROT_WRITE,
                         MAP_PRIVATE | MAP_ANON, -1, 0);
    if (mapping == MAP_FAILED) {
        errno_failure(packet, 0, errno);
        return 0;
    }
    passed(packet, 0, (int64_t)size);
    if (!write_and_read(packet, 1, mapping, 42)) goto cleanup;
    if (mprotect(mapping, size, PROT_READ) != 0) {
        errno_failure(packet, 2, errno);
        goto cleanup;
    }
    uint32_t protected_value = *(volatile uint32_t *)mapping;
    if (protected_value != 42) {
        internal_failure(packet, 2, READBACK_MISMATCH, protected_value);
        goto cleanup;
    }
    passed(packet, 2, 0);
    if (fault) {
        /* Only this complete pre-fault packet plus SIGBUS/SIGSEGV is evidence
         * for the parent. No signal handler or stdio buffer can hide a fault. */
        packet->phase = PEAR_PACKET_ARMED;
        if (emit_packet(packet) != 0) {
            (void)munmap(mapping, size);
            return -1;
        }
        *(volatile uint32_t *)mapping = 84;
        /* Reaching this code must not be accepted as an expected fault. The
         * second packet deliberately exceeds the one-packet protocol. */
        packet->phase = PEAR_PACKET_COMPLETE;
        internal_failure(packet, 3, PROTECTED_WRITE_SUCCEEDED, 84);
        goto cleanup;
    }
    if (mprotect(mapping, size, PROT_READ | PROT_WRITE) != 0) {
        errno_failure(packet, 3, errno);
        goto cleanup;
    }
    passed(packet, 3, 0);
    (void)write_and_read(packet, 4, mapping, 84);

cleanup:
    release_mapping(packet, 5, mapping, size);
    return 0;
}

static void low_address_probe(pear_baseline_packet *packet, size_t size) {
    const mach_vm_address_t requested = UINT64_C(0x20000000);
    mach_vm_address_t address = requested;
    /* FIXED alone never replaces an existing mapping. Keep the executable's
     * normal PAGEZERO and do not use VM_FLAGS_OVERWRITE or a linker override. */
    kern_return_t result = mach_vm_allocate(mach_task_self(), &address,
                                            (mach_vm_size_t)size, VM_FLAGS_FIXED);
    if (result != KERN_SUCCESS) {
        /* This aligned, fixed request can be outside the current process's
         * allocatable address range: the normal ARM64 executable retains a
         * 4 GiB PAGEZERO. A rejected address is unavailable in this layout,
         * not evidence that every low-address configuration is unsupported.
         * Keep invalid arguments and other instrumentation errors failed. */
        pear_step_status status =
            result == KERN_INVALID_ADDRESS || result == KERN_NO_SPACE ||
            result == KERN_PROTECTION_FAILURE
            ? PEAR_STEP_UNAVAILABLE : PEAR_STEP_FAILED;
        record_step(packet, 0, status, PEAR_DOMAIN_MACH, result, 0);
        return;
    }
    if (address != requested) {
        internal_failure(packet, 0, LOW_ADDRESS_MISMATCH, (int64_t)address);
    } else {
        passed(packet, 0, (int64_t)address);
        (void)write_and_read(packet, 1, (volatile uint32_t *)(uintptr_t)address, 42);
    }
    result = mach_vm_deallocate(mach_task_self(), address, (mach_vm_size_t)size);
    if (result == KERN_SUCCESS) passed(packet, 2, 0);
    else record_step(packet, 2, PEAR_STEP_FAILED, PEAR_DOMAIN_MACH, result, 0);
}

static void jit_probe(pear_baseline_packet *packet, size_t size) {
    /* A fixed ARM64 leaf: MOV W0, #42; RET. No external or guest code is read. */
    static const uint32_t instructions[] = {
        UINT32_C(0x52800540), UINT32_C(0xd65f03c0)
    };
    void *mapping = mmap(NULL, size, PROT_READ | PROT_WRITE | PROT_EXEC,
                         MAP_PRIVATE | MAP_ANON | MAP_JIT, -1, 0);
    if (mapping == MAP_FAILED) {
        int error = errno;
        pear_step_status status = error == EPERM || error == EACCES
            ? PEAR_STEP_UNAVAILABLE : PEAR_STEP_FAILED;
        record_step(packet, 0, status, PEAR_DOMAIN_ERRNO, error, 0);
        return;
    }
    passed(packet, 0, (int64_t)size);
    if (!pthread_jit_write_protect_supported_np()) {
        record_step(packet, 1, PEAR_STEP_UNAVAILABLE, PEAR_DOMAIN_INTERNAL,
                    JIT_PROTECTION_UNSUPPORTED, 0);
        goto cleanup;
    }
    pthread_jit_write_protect_np(0);
    memcpy(mapping, instructions, sizeof(instructions));
    passed(packet, 1, sizeof(instructions));
    pthread_jit_write_protect_np(1);
    /* These APIs return void. A returned call is recorded independently from
     * the executable leaf's observed value; it is not a permission proof. */
    passed(packet, 2, 0);
    sys_icache_invalidate(mapping, sizeof(instructions));
    passed(packet, 3, sizeof(instructions));
    uint32_t (*leaf)(void) = (uint32_t (*)(void))mapping;
    uint32_t value = leaf();
    if (value == 42) passed(packet, 4, value);
    else internal_failure(packet, 4, JIT_RETURN_MISMATCH, value);

cleanup:
    release_mapping(packet, 5, mapping, size);
}

int pear_baseline_child_main(int argc, char **argv) {
    pear_probe_id probe;
    if (argc != 2) return 2;
    if (strcmp(argv[1], "memory") == 0) probe = PEAR_PROBE_MEMORY;
    else if (strcmp(argv[1], "protection") == 0) probe = PEAR_PROBE_PROTECTION;
    else if (strcmp(argv[1], "low-address") == 0) probe = PEAR_PROBE_LOW_ADDRESS;
    else if (strcmp(argv[1], "jit") == 0) probe = PEAR_PROBE_JIT;
    else return 2;

    /* Refuse to start a probe when core-dump suppression cannot be installed. */
    const struct rlimit core_limit = {0, 0};
    if (setrlimit(RLIMIT_CORE, &core_limit) != 0) return 3;
    long page_size = sysconf(_SC_PAGESIZE);
    if (page_size < (long)sizeof(uint64_t)) return 3;

    pear_baseline_packet packet;
    memset(&packet, 0, sizeof(packet));
    packet.magic = PEAR_BASELINE_MAGIC;
    packet.version = PEAR_BASELINE_VERSION;
    packet.probe = probe;
    packet.phase = PEAR_PACKET_COMPLETE;
    size_t size = (size_t)page_size;
    switch (probe) {
        case PEAR_PROBE_MEMORY:
        case PEAR_PROBE_PROTECTION:
            if (memory_probe(&packet, size, probe == PEAR_PROBE_PROTECTION) != 0)
                return 3;
            break;
        case PEAR_PROBE_LOW_ADDRESS:
            low_address_probe(&packet, size);
            break;
        case PEAR_PROBE_JIT:
            jit_probe(&packet, size);
            break;
        default:
            return 2;
    }
    return emit_packet(&packet) == 0 ? 0 : 3;
}
