# Makefile for trufflehog-local-git-repos.sh
# Provides targets to check for and install trufflehog
# Pattern follows: /Users/lblackb/data/lblackb/git/make-templates/make/Makefile_software.mk

.PHONY: help trufflehog install-trufflehog check clean test uninstall update

SHELL=/bin/bash
UNAME := $(shell uname -s)
UNAME_M := $(shell uname -m)

# Detect OS and architecture
ifeq ($(UNAME),Linux)
	OS := linux
else ifeq ($(UNAME),Darwin)
	OS := darwin
else ifeq ($(UNAME),MINGW32_NT-6.1)
	OS := windows
else ifeq ($(UNAME),MINGW64_NT-6.1)
	OS := windows
else
	OS := linux
endif

# Map architecture
ifeq ($(UNAME_M),x86_64)
	ARCH := amd64
else ifeq ($(UNAME_M),amd64)
	ARCH := amd64
else ifeq ($(UNAME_M),arm64)
	ARCH := arm64
else ifeq ($(UNAME_M),aarch64)
	ARCH := arm64
else
	ARCH := amd64
endif

# Installation directory (defaults to ~/bin)
HOME_DIR := $(shell echo $$HOME)
INSTALL_DIR := $(HOME_DIR)/bin
# Default version (will fetch latest during install if curl/jq available)
TRUFFLEHOG_VERSION := v3.91.2

default: help

help: ## show this help message
	@echo "Trufflehog Local Git Repos - Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  make trufflehog        - Install trufflehog (alias for install-trufflehog)"
	@echo "  make install-trufflehog - Install trufflehog binary"
	@echo "  make check             - Check if trufflehog is installed"
	@echo "  make update            - Update trufflehog to latest version"
	@echo "  make uninstall         - Remove trufflehog binary"
	@echo "  make clean             - Remove downloaded trufflehog files"
	@echo "  make test              - Test the script (requires trufflehog)"
	@echo ""
	@echo "Detected OS: $(OS)"
	@echo "Detected Arch: $(ARCH)"
	@echo "Install directory: $(INSTALL_DIR)"
	@echo "Trufflehog version: $(TRUFFLEHOG_VERSION)"
	@echo ""
	@echo "Examples:"
	@echo "  make trufflehog                    # Install to ~/bin"
	@echo "  INSTALL_DIR=/usr/local/bin make install-trufflehog  # Install to custom location"

trufflehog: install-trufflehog ## install trufflehog (alias)

install-trufflehog: check-install-dir ## install trufflehog binary
	@VERSION="$(TRUFFLEHOG_VERSION)"; \
	if command -v jq >/dev/null 2>&1 && command -v curl >/dev/null 2>&1; then \
		LATEST=$$(curl -s https://api.github.com/repos/trufflesecurity/trufflehog/releases/latest 2>/dev/null | jq -r '.tag_name' 2>/dev/null); \
		if [ -n "$$LATEST" ] && [ "$$LATEST" != "null" ]; then \
			VERSION="$$LATEST"; \
			echo "Latest version available: $$VERSION"; \
		fi; \
	fi; \
	echo "Installing trufflehog $$VERSION for $(OS)/$(ARCH)..."; \
	echo "Install directory: $(INSTALL_DIR)"; \
	if command -v trufflehog >/dev/null 2>&1; then \
		INSTALLED=$$(which trufflehog); \
		echo "✓ trufflehog is already installed: $$INSTALLED"; \
		echo "  Run 'make update' to update to the latest version"; \
		exit 0; \
	fi; \
	$(MAKE) do-install VERSION="$$VERSION"

update: check-install-dir ## update trufflehog to latest version
	@if ! command -v trufflehog >/dev/null 2>&1; then \
		echo "✗ trufflehog is not installed"; \
		echo "  Run 'make install-trufflehog' to install it first"; \
		exit 1; \
	fi; \
	VERSION=""; \
	if command -v jq >/dev/null 2>&1 && command -v curl >/dev/null 2>&1; then \
		LATEST=$$(curl -s https://api.github.com/repos/trufflesecurity/trufflehog/releases/latest 2>/dev/null | jq -r '.tag_name' 2>/dev/null); \
		if [ -n "$$LATEST" ] && [ "$$LATEST" != "null" ]; then \
			VERSION="$$LATEST"; \
			echo "Updating trufflehog to latest version: $$VERSION"; \
		else \
			echo "ERROR: Could not fetch latest version"; \
			exit 1; \
		fi; \
	else \
		echo "ERROR: jq and curl are required to fetch latest version"; \
		echo "  Install jq and curl, or use: TRUFFLEHOG_VERSION=vX.X.X make install-trufflehog"; \
		exit 1; \
	fi; \
	$(MAKE) do-install VERSION="$$VERSION" FORCE=1

check: ## check if trufflehog is installed
	@echo "Checking for trufflehog..."
	@if command -v trufflehog >/dev/null 2>&1; then \
		INSTALLED=$$(which trufflehog); \
		echo "✓ trufflehog is installed: $$INSTALLED"; \
		if trufflehog --version >/dev/null 2>&1; then \
			trufflehog --version; \
		else \
			echo "  (version check failed)"; \
		fi; \
	else \
		echo "✗ trufflehog is not installed"; \
		echo "  Run 'make install-trufflehog' to install it"; \
		exit 1; \
	fi

uninstall: ## remove trufflehog binary
	@if [ ! -f "$(INSTALL_DIR)/trufflehog" ]; then \
		echo "trufflehog is not installed at $(INSTALL_DIR)/trufflehog"; \
		exit 0; \
	fi; \
	echo "Removing trufflehog from $(INSTALL_DIR)/trufflehog..."; \
	rm -f "$(INSTALL_DIR)/trufflehog" && \
		echo "✓ Uninstalled trufflehog" || \
		{ echo "ERROR: Failed to remove trufflehog"; exit 1; }

clean: ## remove downloaded trufflehog files
	@echo "Cleaning up temporary files..."
	@rm -rf /tmp/trufflehog-install
	@TMP_DIRS=$$(find /tmp -maxdepth 1 -type d -name "trufflehog*" 2>/dev/null || true); \
	if [ -n "$$TMP_DIRS" ]; then \
		echo "Removing temporary directories: $$TMP_DIRS"; \
		rm -rf $$TMP_DIRS; \
	fi
	@echo "✓ Cleanup complete"

test: check ## test the script (requires trufflehog)
	@echo "Testing trufflehog-local-git-repos.sh..."
	@if [ ! -f "./trufflehog-local-git-repos.sh" ]; then \
		echo "ERROR: trufflehog-local-git-repos.sh not found"; \
		exit 1; \
	fi
	@bash -n ./trufflehog-local-git-repos.sh && echo "✓ Syntax check passed" || exit 1
	@./trufflehog-local-git-repos.sh -h >/dev/null && echo "✓ Help output works" || exit 1
	@echo "✓ All tests passed"

# Internal targets
.PHONY: check-install-dir do-install verify-install

check-install-dir:
	@# Create install directory if it doesn't exist
	@if [ ! -d "$(INSTALL_DIR)" ]; then \
		mkdir -p "$(INSTALL_DIR)" 2>/dev/null || { \
			echo "ERROR: Cannot create directory $(INSTALL_DIR)"; \
			echo "Please check permissions or choose a different install directory:"; \
			echo "  INSTALL_DIR=/path/to/dir make install-trufflehog"; \
			exit 1; \
		}; \
	fi
	@# Check if we can write to the directory
	@if [ ! -w "$(INSTALL_DIR)" ]; then \
		echo "ERROR: Cannot write to $(INSTALL_DIR)"; \
		echo "Please check permissions or choose a different install directory:"; \
		echo "  INSTALL_DIR=/path/to/dir make install-trufflehog"; \
		exit 1; \
	fi

do-install:
	@if [ -z "$(VERSION)" ]; then \
		echo "ERROR: VERSION not set"; \
		exit 1; \
	fi; \
	mkdir -p "$(INSTALL_DIR)" || { \
		echo "ERROR: Cannot create directory $(INSTALL_DIR)"; \
		exit 1; \
	}; \
	TMP_DIR=$$(mktemp -d) || { \
		echo "ERROR: Cannot create temporary directory"; \
		exit 1; \
	}; \
	trap "rm -rf $$TMP_DIR" EXIT; \
	echo "Downloading trufflehog $$(VERSION)..."; \
	DOWNLOAD_URL="https://github.com/trufflesecurity/trufflehog/releases/download/$$(VERSION)/trufflehog_$${VERSION#v}_$(OS)_$(ARCH).tar.gz"; \
	if ! curl -f -L -o "$$TMP_DIR/trufflehog.tar.gz" "$$DOWNLOAD_URL" 2>/dev/null; then \
		echo "ERROR: Failed to download trufflehog from: $$DOWNLOAD_URL"; \
		echo "  Check that the version exists and your OS/arch is supported"; \
		rm -rf "$$TMP_DIR"; \
		exit 1; \
	fi; \
	echo "Extracting archive..."; \
	if ! tar -xzf "$$TMP_DIR/trufflehog.tar.gz" -C "$$TMP_DIR" 2>/dev/null; then \
		echo "ERROR: Failed to extract archive"; \
		rm -rf "$$TMP_DIR"; \
		exit 1; \
	fi; \
	if [ ! -f "$$TMP_DIR/trufflehog" ]; then \
		echo "ERROR: Binary not found in archive"; \
		rm -rf "$$TMP_DIR"; \
		exit 1; \
	fi; \
	chmod +x "$$TMP_DIR/trufflehog"; \
	if [ "$(FORCE)" = "1" ] && [ -f "$(INSTALL_DIR)/trufflehog" ]; then \
		echo "Removing existing installation..."; \
		rm -f "$(INSTALL_DIR)/trufflehog"; \
	fi; \
	mv "$$TMP_DIR/trufflehog" "$(INSTALL_DIR)/trufflehog" || { \
		echo "ERROR: Failed to move binary to $(INSTALL_DIR)"; \
		rm -rf "$$TMP_DIR"; \
		exit 1; \
	}; \
	rm -rf "$$TMP_DIR"; \
	echo "✓ Installed trufflehog to $(INSTALL_DIR)/trufflehog"; \
	$(MAKE) verify-install

verify-install:
	@if [ ! -f "$(INSTALL_DIR)/trufflehog" ]; then \
		echo "ERROR: Binary not found at $(INSTALL_DIR)/trufflehog"; \
		exit 1; \
	fi; \
	if [ ! -x "$(INSTALL_DIR)/trufflehog" ]; then \
		echo "ERROR: Binary is not executable"; \
		exit 1; \
	fi; \
	if "$(INSTALL_DIR)/trufflehog" --version >/dev/null 2>&1; then \
		echo "✓ Verification passed: $$("$(INSTALL_DIR)/trufflehog" --version 2>/dev/null || echo "version check")"; \
	else \
		echo "WARNING: Binary exists but version check failed"; \
	fi; \
	echo ""; \
	if echo "$$PATH" | grep -q "$(INSTALL_DIR)"; then \
		echo "✓ $(INSTALL_DIR) is in your PATH"; \
	else \
		echo "⚠ $(INSTALL_DIR) is NOT in your PATH"; \
		echo "Add this to your ~/.bashrc or ~/.zshrc:"; \
		echo "  export PATH=\"$(INSTALL_DIR):\$$PATH\""; \
	fi
