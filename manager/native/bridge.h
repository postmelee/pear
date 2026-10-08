#ifndef PEAR_NATIVE_BRIDGE_H
#define PEAR_NATIVE_BRIDGE_H
#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Caller owns both outputs. No allocation, retained pointers or process mutation.
 * Zero means both creation-time fields are valid; other values are errno codes. */
int32_t pear_process_identity(int32_t pid, uint64_t *started_sec, uint64_t *started_usec);
/* Staging mutates only the supplied directory; caller retains/removes the named entry.
 * Hashing uses pread from byte zero without changing the caller's offset. Both calls
 * return errno values, retain no pointers, and must not run in a post-fork child. */
int32_t pear_stage_directory(int32_t parent, uint8_t *name, size_t capacity);
int32_t pear_sha256_fd(int32_t fd, uint64_t limit, uint8_t *digest, uint64_t *bytes);
int32_t pear_mount_info(int32_t fd, uint64_t *flags, int32_t *fsid0, int32_t *fsid1);
#ifdef __cplusplus
}
#endif
#endif
int32_t pear_sha256_bytes(const uint8_t *data, size_t size, uint8_t *digest);
