# Top-level dispatcher for Daisy Seed firmware projects in this repo.
#
# Each project lives under projects/<name>/ with its own Makefile that
# includes libDaisy/core/Makefile. This file forwards build/flash/clean to
# the right project and hosts the shared serial-monitor helpers.

PROJECTS := $(sort $(notdir $(patsubst %/,%,$(dir $(wildcard projects/*/Makefile)))))

# Override on the command line: `make PROJECT=calibrate-output program`
PROJECT ?= test-midi

LIBDAISY_DIR := libDaisy
DAISYSP_DIR  := DaisySP

.DEFAULT_GOAL := all

all: $(PROJECT)

help:
	@echo ""
	@echo "Projects in this repo: $(PROJECTS)"
	@echo "Default project:       $(PROJECT)  (override with PROJECT=<name>)"
	@echo ""
	@echo "Build:"
	@echo "  make                        Build the default project"
	@echo "  make <project>              Build a specific project (e.g. 'make test-midi')"
	@echo "  make PROJECT=<name>         Same as above via variable"
	@echo "  make all-projects           Build every project"
	@echo ""
	@echo "Flash via USB DFU (hold BOOT, tap RESET, then run):"
	@echo "  make program                Flash the default project"
	@echo "  make program-<project>      Flash a specific project"
	@echo "  make program-boot-<project> Flash the Daisy bootloader for a project"
	@echo ""
	@echo "Serial monitor (host-side, picks whichever Daisy is attached):"
	@echo "  make monitor                Open USB-CDC port at 115200 with screen"
	@echo "  make monitor-port           Print the /dev/tty.usbmodem* path"
	@echo ""
	@echo "Housekeeping:"
	@echo "  make libs                   (Re)build libDaisy + DaisySP archives once"
	@echo "  make libs-clean             Clean libDaisy + DaisySP archives"
	@echo "  make clean                  Wipe every project's build/ dir"
	@echo "  make clean-<project>        Wipe one project's build/ dir"
	@echo "  make distclean              clean + libs-clean"
	@echo "  make lint                   clang-format dry-run on every project"
	@echo "  make list                   List projects, one per line"
	@echo ""

list:
	@for p in $(PROJECTS); do echo $$p; done

# --- Per-project pattern rules ------------------------------------------
# Forwards into projects/<name>/Makefile, which actually invokes the
# libDaisy core Makefile. Each project gets its own build/ dir.

$(PROJECTS):
	$(MAKE) -C projects/$@

all-projects: $(PROJECTS)

# `make program` flashes the default project. `make program-<project>`
# flashes a specific one. `program-boot-%` is matched before `program-%`
# because GNU make prefers the shortest-stem pattern when both match.
program: program-$(PROJECT)

program-boot-%:
	$(MAKE) -C projects/$* program-boot

program-%:
	$(MAKE) -C projects/$* program-dfu

clean-%:
	$(MAKE) -C projects/$* clean

clean: $(addprefix clean-,$(PROJECTS))

lint:
	@set -e; for p in $(PROJECTS); do echo "==> $$p"; $(MAKE) -C projects/$$p lint; done

libs:
	$(MAKE) -C $(LIBDAISY_DIR)
	$(MAKE) -C $(DAISYSP_DIR)
	$(MAKE) -C $(DAISYSP_DIR)/DaisySP-LGPL

libs-clean:
	$(MAKE) -C $(LIBDAISY_DIR) clean
	$(MAKE) -C $(DAISYSP_DIR) clean
	$(MAKE) -C $(DAISYSP_DIR)/DaisySP-LGPL clean

distclean: clean libs-clean

# --- Serial monitor helpers ---------------------------------------------
# The Seed presents a USB CDC port at /dev/tty.usbmodem<chipUID> on macOS
# once user firmware is running with hw.StartLog(...). The device name
# carries the STM32's unique-id, not "Daisy", so we just grab the first
# usbmodem device. Override DAISY_SERIAL=/dev/tty.usbmodemXXX if you have
# multiple usbmodem devices plugged in.
DAISY_SERIAL ?= $(firstword $(wildcard /dev/tty.usbmodem*))

monitor:
	@ports="$(wildcard /dev/tty.usbmodem*)"; \
	count=$$(echo $$ports | wc -w | tr -d ' '); \
	if [ -z "$$ports" ]; then \
	  echo "No USB-serial port found at /dev/tty.usbmodem*"; \
	  echo "(make sure firmware with hw.StartLog() is running, not in DFU mode)"; \
	  exit 1; \
	elif [ $$count -gt 1 ]; then \
	  echo "Multiple usbmodem ports found:"; \
	  for p in $$ports; do echo "  $$p"; done; \
	  echo "Re-run as: make monitor DAISY_SERIAL=/dev/tty.usbmodemXXX"; \
	  exit 1; \
	fi; \
	echo "Opening $(DAISY_SERIAL) — press Ctrl-A then K to quit screen"; \
	screen $(DAISY_SERIAL) 115200

monitor-port:
	@echo "$(DAISY_SERIAL)"

.PHONY: all help list all-projects program clean distclean libs libs-clean lint \
        monitor monitor-port $(PROJECTS)
