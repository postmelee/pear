CC = xcrun clang
CFLAGS = -std=c11 -O2 -Wall -Wextra -Werror
ARCH_FLAGS = -arch arm64 -mmacosx-version-min=13.0
BUILD_DIR = ../../.build/host-probe
TARGET = $(BUILD_DIR)/pear-host-probe
BASELINE = $(BUILD_DIR)/pear-baseline-probe
CHILD = $(BUILD_DIR)/pear-probe-child
PROCESS = $(BUILD_DIR)/pear-process-probe
LAYOUT = $(BUILD_DIR)/pear-process-probe-layout
PROCESS_SOURCES = process_main.c process_child.c process_evaluate.c baseline_child.c baseline_evaluate.c child_runner.c observations.c
FRAMEWORKS = -framework Security -framework CoreFoundation

.PHONY: all
all: $(TARGET) $(BASELINE) $(CHILD) $(PROCESS) $(LAYOUT)

$(TARGET): main.c observations.c observations.h Makefile
	mkdir -p "$(BUILD_DIR)"
	$(CC) $(CFLAGS) $(ARCH_FLAGS) main.c observations.c $(FRAMEWORKS) -o "$@"

$(BASELINE): baseline_main.c child_runner.c baseline_evaluate.c baseline.h observations.c observations.h Makefile
	mkdir -p "$(BUILD_DIR)"
	$(CC) $(CFLAGS) $(ARCH_FLAGS) baseline_main.c child_runner.c baseline_evaluate.c observations.c $(FRAMEWORKS) -o "$@"

$(CHILD): baseline_child.c baseline_child_entry.c baseline.h Makefile
	mkdir -p "$(BUILD_DIR)"
	$(CC) $(CFLAGS) $(ARCH_FLAGS) baseline_child.c baseline_child_entry.c -o "$@"

$(PROCESS): $(PROCESS_SOURCES) baseline.h observations.h Makefile
	mkdir -p "$(BUILD_DIR)"
	$(CC) $(CFLAGS) $(ARCH_FLAGS) $(PROCESS_SOURCES) $(FRAMEWORKS) -o "$@"

$(LAYOUT): $(PROCESS_SOURCES) baseline.h observations.h Makefile
	mkdir -p "$(BUILD_DIR)"
	$(CC) $(CFLAGS) $(ARCH_FLAGS) -Wl,-x86_64_layout_emulation,-pagezero_size,0x10000 $(PROCESS_SOURCES) $(FRAMEWORKS) -o "$@"
