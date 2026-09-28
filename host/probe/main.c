#include "observations.h"

#include <string.h>

int main(int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "--help") == 0) {
        puts("Usage: pear-host-probe [--help]\n"
             "Write bounded JSON observations about this process and host.\n"
             "No runtime capability or game compatibility is qualified.");
        return 0;
    }
    if (argc != 1) {
        fputs("Usage: pear-host-probe [--help]\n", stderr);
        return 2;
    }
    pear_report report;
    pear_collect(pear_system_source(), &report);
    if (pear_write_json(stdout, &report) != 0 || fflush(stdout) != 0) {
        fputs("Unable to write the diagnostic report.\n", stderr);
        return 1;
    }
    return 0;
}
