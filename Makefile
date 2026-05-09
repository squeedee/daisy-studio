# Daisy Studio — 3D viewer build.
# Run `make help` for the list of targets.
#
# Requires `uv` (https://docs.astral.sh/uv/). Build dependencies are declared
# inline in docs/3d-viewer/build.py via PEP 723; uv resolves and caches them
# automatically — no virtualenv to manage.

UV         ?= uv
PORT       ?= 8765
RES        ?= 8192
VIEWER_DIR := docs/3d-viewer
BUILD      := $(UV) run $(VIEWER_DIR)/build.py

.DEFAULT_GOAL := help

## help: list available targets
help:
	@printf "Usage: make <target>\n\nTargets:\n"
	@awk '/^## / { sub(/^## /,""); split($$0,a,":"); printf "  \033[36m%-12s\033[0m %s\n", a[1], substr($$0,length(a[1])+2) }' $(MAKEFILE_LIST)
	@printf "\nVariables (override on the command line):\n"
	@printf "  RES=N       texture resolution for build (default %s)\n" $(RES)
	@printf "  PORT=N      local server port (default %s)\n" $(PORT)
	@printf "\nExamples:\n  make build RES=8192\n  make serve PORT=9000\n"

## build: full rebuild — model.glb + docs.html (composite mode)
build:
	$(BUILD) composite --resolution $(RES)

## glb: rebuild model.glb + docs.html (alias for build)
glb: build

## docs: render docs.md → docs.html (fast, no GLB rebuild)
docs:
	$(BUILD) docs

## baked: alternative GLB build using kicad-cli raytraced render as the texture
baked:
	$(BUILD) baked --resolution $(RES)

## serve: local Python http.server in $(VIEWER_DIR) on $(PORT)
serve:
	cd $(VIEWER_DIR) && python3 -m http.server $(PORT) --bind 127.0.0.1

## deploy: rebuild at 8192 then push docs/3d-viewer/ to the gh-pages branch.
##         GitHub Pages serves from there. Local build IS the deploy.
deploy:
	$(MAKE) build
	./scripts/deploy.sh

## clean: remove generated GLB / textures / docs.html
clean:
	rm -f $(VIEWER_DIR)/model.glb $(VIEWER_DIR)/docs.html
	rm -rf $(VIEWER_DIR)/textures

.PHONY: help build glb docs baked serve deploy clean
