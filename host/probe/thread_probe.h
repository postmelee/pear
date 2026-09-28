#ifndef PEAR_THREAD_PROBE_H
#define PEAR_THREAD_PROBE_H

#include "baseline.h"
#include <mach/kern_return.h>
#include <stdint.h>

#define PEAR_THREAD_LITMUS_TRIALS 10000U

typedef kern_return_t (*pear_thread_policy_function)(uint32_t enable);

void pear_thread_probe(pear_baseline_packet *packet);
void pear_thread_litmus_probe(pear_baseline_packet *packet);

/* Payload words are accessed only by these assembly functions during trials. */
void pear_litmus_reset(uint32_t *data, uint32_t *flag);
void pear_litmus_write(uint32_t *data, uint32_t *flag);
uint64_t pear_litmus_read(const uint32_t *data, const uint32_t *flag);

#ifdef PEAR_THREAD_PROBE_TEST
/* The fixture supplies this symbol only in its separately compiled test build. */
pear_thread_policy_function pear_test_thread_policy_resolve(void);
#endif

#endif
