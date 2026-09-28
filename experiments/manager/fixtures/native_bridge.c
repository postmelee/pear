#include "native_bridge.h"
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
