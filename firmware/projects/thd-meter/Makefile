# THD meter firmware for the Daisy Seed.
# Coherent / windowed FFT-based THD analyzer with USB-CDC control + reporting.
TARGET = ThdMeter

CPP_SOURCES = ThdMeter.cpp

# Run from external QSPI flash (8 MB) — internal FLASH (128 KB) can't hold
# libDaisy + CMSIS-DSP RFFT chain + ThdMeter together. Requires the Daisy
# bootloader to be flashed to internal FLASH once via `make program-boot`
# (Seed in DFU mode). After that, `make program-dfu` writes the app to QSPI.
APP_TYPE = BOOT_QSPI

LIBDAISY_DIR = ../../libDaisy
DAISYSP_DIR  = ../../DaisySP

# CMSIS-DSP — minimal source set for arm_rfft_fast_f32 at N = 4096.
# The unity files (TransformFunctions.c / CommonTables.c) include every
# transform variant (q15, q31, f64, f16, DCT, …) and overflow FLASH even
# with --gc-sections. List only what we need.
CMSIS_DSP_DIR = $(LIBDAISY_DIR)/Drivers/CMSIS-DSP/Source
C_SOURCES += \
$(CMSIS_DSP_DIR)/TransformFunctions/arm_rfft_fast_f32.c \
$(CMSIS_DSP_DIR)/TransformFunctions/arm_rfft_fast_init_f32.c \
$(CMSIS_DSP_DIR)/TransformFunctions/arm_cfft_f32.c \
$(CMSIS_DSP_DIR)/TransformFunctions/arm_cfft_init_f32.c \
$(CMSIS_DSP_DIR)/TransformFunctions/arm_cfft_radix8_f32.c \
$(CMSIS_DSP_DIR)/TransformFunctions/arm_bitreversal2.c \
$(CMSIS_DSP_DIR)/CommonTables/arm_const_structs.c \
$(CMSIS_DSP_DIR)/CommonTables/arm_common_tables.c

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
