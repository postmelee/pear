#ifndef PEAR_NATIVE_BRIDGE_H
#define PEAR_NATIVE_BRIDGE_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Caller owns both outputs. No allocation, retained pointers or process mutation.
 * Zero means both creation-time fields are valid; other values are errno codes. */
int32_t pear_process_identity(int32_t pid, uint64_t *started_sec, uint64_t *started_usec);
#ifdef __cplusplus
}
#endif
#endif
