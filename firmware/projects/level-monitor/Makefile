# Level monitor firmware for the Daisy Seed.
# Stereo audio passthrough + USB-CDC peak/RMS/peak-hold reporting.
TARGET = LevelMonitor

CPP_SOURCES = LevelMonitor.cpp

LIBDAISY_DIR = ../../libDaisy
DAISYSP_DIR  = ../../DaisySP

SYSTEM_FILES_DIR = $(LIBDAISY_DIR)/core
include $(SYSTEM_FILES_DIR)/Makefile

LDFLAGS += -u _printf_float

all: libs
	$(MAKE) build/$(TARGET).elf build/$(TARGET).hex build/$(TARGET).bin

libs:
	$(MAKE) -C $(LIBDAISY_DIR)
	$(MAKE) -C $(DAISYSP_DIR)
	$(MAKE) -C $(DAISYSP_DIR)/DaisySP-LGPL

lint:
	clang-format --dry-run --Werror $(CPP_SOURCES)

.PHONY: all libs lint
