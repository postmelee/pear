#include "baseline.h"

#include <errno.h>
#include <mach/mach.h>
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <unistd.h>

#if !defined(__aarch64__) && !defined(__arm64__)
#error "The process capability child must be built for ARM64."
#endif

enum { GUEST_PAGE_SIZE = 4096, MAPPING_SIZE = 3 * GUEST_PAGE_SIZE };

/* Stable internal error codes; never substitute these for errno or Mach errors.
 * 10: user pages are not 4 KiB; 11: sentinel readback mismatch;
 * 12: protected access unexpectedly returned; 13: fixed mapping moved;
 * 14: replacement page was not zero-filled; 15: invalid page-size result. */
enum {
    USER_PAGE_SIZE_UNAVAILABLE = 10,
    SENTINEL_MISMATCH,
    PROTECTED_ACCESS_SUCCEEDED,
    REPLACEMENT_ADDRESS_MISMATCH,
    REPLACEMENT_NOT_ZERO,
    PAGE_SIZE_INVALID
};

static const uint32_t initial_sentinels[] = {
    UINT32_C(0x11223344), UINT32_C(0x55667788), UINT32_C(0x13579bdf)
};
static const uint32_t updated_neighbors[] = {
    UINT32_C(0x2468ace0), UINT32_C(0x76543210)
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
    while (remaining != 0) {
        ssize_t amount = write(STDOUT_FILENO, bytes, remaining);
        if (amount < 0 && errno == EINTR) continue;
        if (amount <= 0) return -1;
        bytes += (size_t)amount;
        remaining -= (size_t)amount;
    }
    return 0;
}

static void geometry_probe(pear_baseline_packet *packet) {
    errno = 0;
    long user_page = sysconf(_SC_PAGESIZE);
    if (user_page > 0) passed(packet, 0, user_page);
    else if (errno != 0) errno_failure(packet, 0, errno);
    else internal_failure(packet, 0, PAGE_SIZE_INVALID, user_page);
    if (packet->steps[0].status != PEAR_STEP_PASSED) return;

    if (vm_page_size > 0) passed(packet, 1, vm_page_size);
    else {
        internal_failure(packet, 1, PAGE_SIZE_INVALID, vm_page_size);
        return;
    }

    host_t host = mach_host_self();
    vm_size_t kernel_page = 0;
    kern_return_t result = host_page_size(host, &kernel_page);
    kern_return_t released = mach_port_deallocate(mach_task_self(), host);
    if (result != KERN_SUCCESS) {
        record_step(packet, 2, PEAR_STEP_FAILED, PEAR_DOMAIN_MACH, result, 0);
    } else if (released != KERN_SUCCESS) {
        record_step(packet, 2, PEAR_STEP_FAILED, PEAR_DOMAIN_MACH, released,
                    kernel_page);
    } else if (kernel_page == 0) {
        internal_failure(packet, 2, PAGE_SIZE_INVALID, kernel_page);
    } else passed(packet, 2, kernel_page);
}

static volatile uint32_t *page_at(void *mapping, size_t index) {
    return (volatile uint32_t *)((unsigned char *)mapping + index * GUEST_PAGE_SIZE);
}

/* Check both ends of each owned page, including the boundary next to its
 * neighbor. Volatile accesses keep the tested memory operations observable. */
static void write_sentinels(volatile uint32_t *page, uint32_t value) {
    page[0] = value;
    page[GUEST_PAGE_SIZE / sizeof(uint32_t) - 1] = value ^ UINT32_C(0xffffffff);
}

static bool check_sentinels(volatile uint32_t *page, uint32_t value) {
    uint32_t first = page[0];
    uint32_t last = page[GUEST_PAGE_SIZE / sizeof(uint32_t) - 1];
    return first == value && last == (value ^ UINT32_C(0xffffffff));
}

static unsigned neighbor_mask(void *mapping, const uint32_t values[2]) {
    unsigned mask = 0;
    if (check_sentinels(page_at(mapping, 0), values[0])) mask |= 1;
    if (check_sentinels(page_at(mapping, 2), values[1])) mask |= 2;
    return mask;
}

static bool check_neighbors(pear_baseline_packet *packet, size_t index,
                            void *mapping, bool update) {
    const uint32_t before[] = {initial_sentinels[0], initial_sentinels[2]};
    unsigned mask = neighbor_mask(mapping, update ? before : updated_neighbors);
    if (mask != 3) {
        internal_failure(packet, index, SENTINEL_MISMATCH, mask);
        return false;
    }
    if (update) {
        write_sentinels(page_at(mapping, 0), updated_neighbors[0]);
        write_sentinels(page_at(mapping, 2), updated_neighbors[1]);
        mask = neighbor_mask(mapping, updated_neighbors);
        if (mask != 3) {
            internal_failure(packet, index, SENTINEL_MISMATCH, mask);
            return false;
        }
    }
    return true;
}

static int arm_and_access(pear_baseline_packet *packet, void *mapping,
                          bool write_fault) {
    packet->phase = PEAR_PACKET_ARMED;
    if (emit_packet(packet) != 0) return -1;
    volatile uint32_t *middle = page_at(mapping, 1);
    uint32_t observed;
    if (write_fault) {
        *middle = 84;
        observed = 84;
    } else observed = *middle;
    /* A second packet must exceed the parent's packet limit. Success is only
     * the armed packet plus the actual protection-fault signal. */
    packet->phase = PEAR_PACKET_COMPLETE;
    internal_failure(packet, 3, PROTECTED_ACCESS_SUCCEEDED, observed);
    return 0;
}

static int memory_probe(pear_baseline_packet *packet, pear_probe_id probe) {
    errno = 0;
    long user_page = sysconf(_SC_PAGESIZE);
    if (user_page <= 0) {
        if (errno != 0) errno_failure(packet, 0, errno);
        else internal_failure(packet, 0, PAGE_SIZE_INVALID, user_page);
        return 0;
    }
    if (user_page != GUEST_PAGE_SIZE) {
        record_step(packet, 0, PEAR_STEP_UNAVAILABLE, PEAR_DOMAIN_INTERNAL,
                    USER_PAGE_SIZE_UNAVAILABLE, user_page);
        return 0;
    }
    void *mapping = mmap(NULL, MAPPING_SIZE, PROT_READ | PROT_WRITE,
                         MAP_PRIVATE | MAP_ANON, -1, 0);
    if (mapping == MAP_FAILED) {
        errno_failure(packet, 0, errno);
        return 0;
    }
    passed(packet, 0, MAPPING_SIZE);
    unsigned mask = 0;
    for (size_t i = 0; i != 3; ++i) {
        volatile uint32_t *page = page_at(mapping, i);
        write_sentinels(page, initial_sentinels[i]);
        if (check_sentinels(page, initial_sentinels[i])) mask |= 1u << i;
    }
    int result = 0;
    if (mask != 7) {
        internal_failure(packet, 1, SENTINEL_MISMATCH, mask);
        goto cleanup;
    }
    passed(packet, 1, mask);
    void *middle = (unsigned char *)mapping + GUEST_PAGE_SIZE;
    bool subpage = probe == PEAR_PROBE_SUBPAGE || probe == PEAR_PROBE_SUBPAGE_FAULT;
    bool fault = probe == PEAR_PROBE_SUBPAGE_FAULT ||
                 probe == PEAR_PROBE_RECOMMIT_FAULT;
    if (subpage) {
        if (mprotect(middle, GUEST_PAGE_SIZE, PROT_READ) != 0) {
            errno_failure(packet, 2, errno);
            goto cleanup;
        }
        if (!check_sentinels(middle, initial_sentinels[1])) {
            internal_failure(packet, 2, SENTINEL_MISMATCH, 0);
            goto cleanup;
        }
        if (!check_neighbors(packet, 2, mapping, true)) goto cleanup;
        passed(packet, 2, 0);
        if (fault) {
            result = arm_and_access(packet, mapping, true);
            goto cleanup;
        }
        if (mprotect(middle, GUEST_PAGE_SIZE, PROT_READ | PROT_WRITE) != 0) {
            errno_failure(packet, 3, errno);
            goto cleanup;
        }
        *(volatile uint32_t *)middle = 84;
        uint32_t observed = *(volatile uint32_t *)middle;
        if (observed != 84) {
            internal_failure(packet, 3, SENTINEL_MISMATCH, observed);
            goto cleanup;
        }
        passed(packet, 3, observed);
        if (!check_neighbors(packet, 4, mapping, false)) goto cleanup;
        passed(packet, 4, 3);
    } else {
        /* Replace only the middle page of this live owned mapping. MAP_FIXED
         * must never target arbitrary addresses or mappings owned by others.
         * This checks anonymous replacement and recommit, not MADV semantics. */
        void *replacement = mmap(middle, GUEST_PAGE_SIZE, PROT_NONE,
                                  MAP_FIXED | MAP_PRIVATE | MAP_ANON, -1, 0);
        if (replacement == MAP_FAILED) {
            errno_failure(packet, 2, errno);
            goto cleanup;
        }
        if (replacement != middle) {
            internal_failure(packet, 2, REPLACEMENT_ADDRESS_MISMATCH, 0);
            (void)munmap(replacement, GUEST_PAGE_SIZE);
            goto cleanup;
        }
        if (fault) {
            if (!check_neighbors(packet, 2, mapping, true)) goto cleanup;
            passed(packet, 2, 0);
            result = arm_and_access(packet, mapping, false);
            goto cleanup;
        }
        passed(packet, 2, 0);
        if (!check_neighbors(packet, 3, mapping, true)) goto cleanup;
        passed(packet, 3, 3);
        if (mprotect(middle, GUEST_PAGE_SIZE, PROT_READ | PROT_WRITE) != 0) {
            errno_failure(packet, 4, errno);
            goto cleanup;
        }
        volatile unsigned char *bytes = middle;
        for (size_t i = 0; i != GUEST_PAGE_SIZE; ++i) {
            if (bytes[i] != 0) {
                internal_failure(packet, 4, REPLACEMENT_NOT_ZERO, (int64_t)i);
                goto cleanup;
            }
        }
        *(volatile uint32_t *)middle = 42;
        uint32_t observed = *(volatile uint32_t *)middle;
        if (observed != 42) {
            internal_failure(packet, 4, SENTINEL_MISMATCH, observed);
            goto cleanup;
        }
        if (!check_neighbors(packet, 4, mapping, false)) goto cleanup;
        passed(packet, 4, observed);
    }

cleanup:
    if (munmap(mapping, MAPPING_SIZE) == 0) passed(packet, 5, 0);
    else errno_failure(packet, 5, errno);
    return result;
}

int pear_process_child_main(pear_probe_id probe) {
    if (probe < PEAR_PROBE_GEOMETRY || probe > PEAR_PROBE_RECOMMIT_FAULT) return 2;
    const struct rlimit core_limit = {0, 0};
    if (setrlimit(RLIMIT_CORE, &core_limit) != 0) return 3;
    pear_baseline_packet packet;
    memset(&packet, 0, sizeof(packet));
    packet.magic = PEAR_BASELINE_MAGIC;
    packet.version = PEAR_BASELINE_VERSION;
    packet.probe = probe;
    packet.phase = PEAR_PACKET_COMPLETE;
    if (probe == PEAR_PROBE_GEOMETRY) geometry_probe(&packet);
    else if (memory_probe(&packet, probe) != 0) return 3;
    return emit_packet(&packet) == 0 ? 0 : 3;
}
