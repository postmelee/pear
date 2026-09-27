CC = xcrun clang
CFLAGS = -std=c11 -O2 -Wall -Wextra -Werror
ARCH_FLAGS = -arch arm64 -mmacosx-version-min=13.0
BUILD_DIR = ../../.build/host-probe
TARGET = $(BUILD_DIR)/pear-host-probe
BASELINE = $(BUILD_DIR)/pear-baseline-probe
CHILD = $(BUILD_DIR)/pear-probe-child
FRAMEWORKS = -framework Security -framework CoreFoundation

.PHONY: all
all: $(TARGET) $(BASELINE) $(CHILD)

$(TARGET): main.c observations.c observations.h
	mkdir -p "$(BUILD_DIR)"
	$(CC) $(CFLAGS) $(ARCH_FLAGS) main.c observations.c $(FRAMEWORKS) -o "$@"

$(BASELINE): baseline_main.c child_runner.c baseline_evaluate.c baseline.h observations.c observations.h
	mkdir -p "$(BUILD_DIR)"
	$(CC) $(CFLAGS) $(ARCH_FLAGS) baseline_main.c child_runner.c baseline_evaluate.c observations.c $(FRAMEWORKS) -o "$@"

$(CHILD): baseline_child.c baseline.h
	mkdir -p "$(BUILD_DIR)"
	$(CC) $(CFLAGS) $(ARCH_FLAGS) baseline_child.c -o "$@"
