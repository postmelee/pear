#include "bridge.h"
#include <errno.h>
#include <libproc.h>
#include <string.h>
#include <sys/proc_info.h>
int32_t pear_process_identity(int32_t pid, uint64_t *started_sec, uint64_t *started_usec) {
    if (pid <= 0 || !started_sec || !started_usec) return EINVAL;
    struct proc_bsdinfo info;
    memset(&info, 0, sizeof(info));
    errno = 0;
    int bytes = proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &info, sizeof(info));
    if (bytes != (int)sizeof(info)) return errno ? errno : EIO;
    *started_sec = info.pbi_start_tvsec;
    *started_usec = info.pbi_start_tvusec;
    return 0;
}

#include <CommonCrypto/CommonDigest.h>
#include <fcntl.h>
#include <limits.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>

int32_t pear_stage_directory(int32_t parent, uint8_t *name, size_t capacity) {
    if (!name || capacity != sizeof("stage.XXXXXX") ||
        memcmp(name, "stage.XXXXXX", sizeof("stage.XXXXXX")) != 0) return EINVAL;
    return mkdtempat_np(parent, (char *)name) ? 0 : (errno ? errno : EIO);
}
int32_t pear_sha256_fd(int32_t fd, uint64_t limit, uint8_t *digest, uint64_t *bytes) {
    if (!digest || !bytes) return EINVAL;
    memset(digest, 0, CC_SHA256_DIGEST_LENGTH); *bytes = 0;
    if (limit > INT64_MAX) return EINVAL;
    struct stat before, after;
    if (fstat(fd, &before) != 0) return errno;
    if (!S_ISREG(before.st_mode)) return EINVAL;
    if (before.st_size < 0 || (uint64_t)before.st_size > limit) return EFBIG;
    CC_SHA256_CTX context;
    if (!CC_SHA256_Init(&context)) return EIO;
    unsigned char buffer[1024 * 1024];
    uint64_t total = 0;
    for (;;) {
        size_t amount = sizeof(buffer);
        if (limit - total < amount) amount = (size_t)(limit - total) + 1;
        ssize_t n = pread(fd, buffer, amount, (off_t)total);
        if (n < 0) { if (errno == EINTR) continue; return errno; }
        if (n == 0) break;
        if ((uint64_t)n > limit - total) return EFBIG;
        if (!CC_SHA256_Update(&context, buffer, (CC_LONG)n)) return EIO;
        total += (uint64_t)n;
    }
    if (fstat(fd, &after) != 0) return errno;
    if (total != (uint64_t)before.st_size || before.st_size != after.st_size ||
        before.st_mtimespec.tv_sec != after.st_mtimespec.tv_sec ||
        before.st_mtimespec.tv_nsec != after.st_mtimespec.tv_nsec ||
        before.st_ctimespec.tv_sec != after.st_ctimespec.tv_sec ||
        before.st_ctimespec.tv_nsec != after.st_ctimespec.tv_nsec) return ESTALE;
    if (!CC_SHA256_Final(digest, &context)) return EIO;
    *bytes = total;
    return 0;
}

#include <sys/mount.h>
int32_t pear_mount_info(int32_t fd, uint64_t *flags, int32_t *fsid0, int32_t *fsid1) {
    if (!flags || !fsid0 || !fsid1) return EINVAL;
    struct statfs info;
    memset(&info, 0, sizeof(info));
    if (fstatfs(fd, &info) != 0) return errno;
    *flags = info.f_flags; *fsid0 = info.f_fsid.val[0]; *fsid1 = info.f_fsid.val[1];
    return 0;
}
int32_t pear_sha256_bytes(const uint8_t *data, size_t size, uint8_t *digest) {
    if (!data || !digest || size > 256 * 1024) return EINVAL;
    memset(digest, 0, CC_SHA256_DIGEST_LENGTH);
    return CC_SHA256(data, (CC_LONG)size, digest) ? 0 : EIO;
}
