#ifndef PEAR_OBSERVATIONS_H
#define PEAR_OBSERVATIONS_H

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

#define PEAR_PROBE_VERSION "0.1.0"
#define PEAR_TEXT_CAPACITY 256
#define PEAR_SYMBOL_COUNT 4

typedef enum {
    PEAR_UNAVAILABLE = 0,
    PEAR_OBSERVED,
    PEAR_FAILED
} pear_status;

typedef enum { PEAR_TEXT, PEAR_INTEGER, PEAR_BOOLEAN } pear_value_kind;
typedef enum {
    PEAR_ERROR_NONE = 0,
    PEAR_ERROR_ERRNO,
    PEAR_ERROR_OSSTATUS,
    PEAR_ERROR_INTERNAL
} pear_error_domain;

/* Fixed-capacity storage keeps every observation and serialized report bounded. */
typedef struct {
    pear_status status;
    pear_value_kind kind;
    char text[PEAR_TEXT_CAPACITY];
    int64_t number;
    pear_error_domain error_domain;
    int64_t error_code;
} pear_observation;

/* Fixtures substitute platform observations at link time, never through CLI flags. */
typedef struct {
    void *context;
    pear_observation (*architecture)(void *context);
    pear_observation (*sysctl_text)(void *context, const char *name);
    pear_observation (*sysctl_integer)(void *context, const char *name);
    pear_observation (*page_size)(void *context);
    pear_observation (*symbol)(void *context, const char *name);
    pear_observation (*signature)(void *context);
} pear_source;

typedef struct {
    pear_observation architecture;
    pear_observation translated;
    pear_observation os_version;
    pear_observation os_build;
    pear_observation page_size_bytes;
    pear_observation symbols[PEAR_SYMBOL_COUNT];
    pear_observation signature_category;
} pear_report;

extern const char *const pear_symbol_names[PEAR_SYMBOL_COUNT];

pear_observation pear_observed_text(const char *value);
pear_observation pear_observed_integer(int64_t value);
pear_observation pear_observed_boolean(bool value);
pear_observation pear_observation_error(pear_value_kind kind, pear_status status,
                                      pear_error_domain domain, int64_t code);
const pear_source *pear_system_source(void);
void pear_collect(const pear_source *source, pear_report *report);
/* Returns 0 on complete output, -1 on an output error. */
int pear_write_json(FILE *stream, const pear_report *report);

#endif
