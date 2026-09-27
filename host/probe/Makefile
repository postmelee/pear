CC = xcrun clang
CFLAGS = -std=c11 -O2 -Wall -Wextra -Werror
BUILD_DIR = ../../.build/host-probe
TARGET = $(BUILD_DIR)/pear-host-probe

.PHONY: all
all: $(TARGET)

$(TARGET): main.c observations.c observations.h
	mkdir -p "$(BUILD_DIR)"
	$(CC) $(CFLAGS) -arch arm64 -mmacosx-version-min=13.0 main.c observations.c \
		-framework Security -framework CoreFoundation -o "$(TARGET)"
