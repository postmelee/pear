/* Self-owned declared dependency; each build has a distinct observable marker. */
#ifndef FIXTURE_ALTERNATE
#define FIXTURE_ALTERNATE 0
#endif
const char *fixture_marker(void) { return FIXTURE_ALTERNATE ? "alternate" : "approved!"; }
