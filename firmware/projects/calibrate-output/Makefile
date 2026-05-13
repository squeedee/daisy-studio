# 1 kHz sine output for verifying the Daisy Seed's audio path.
TARGET = testoutput

CPP_SOURCES = TestOutput.cpp

LIBDAISY_DIR = ../../libDaisy
DAISYSP_DIR  = ../../DaisySP

SYSTEM_FILES_DIR = $(LIBDAISY_DIR)/core
include $(SYSTEM_FILES_DIR)/Makefile

all: libs
	$(MAKE) build/$(TARGET).elf build/$(TARGET).hex build/$(TARGET).bin

libs:
	$(MAKE) -C $(LIBDAISY_DIR)
	$(MAKE) -C $(DAISYSP_DIR)
	$(MAKE) -C $(DAISYSP_DIR)/DaisySP-LGPL

lint:
	clang-format --dry-run --Werror $(CPP_SOURCES)

.PHONY: all libs lint
