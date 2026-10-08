/* Self-owned finite Stage 2 loader fixture; no game/runtime delegation. */
#include <unistd.h>
extern const char *fixture_marker(void);
int main(void) {
    const char *marker = fixture_marker();
    return write(STDOUT_FILENO, marker, 9) == 9 ? 0 : 1;
}
