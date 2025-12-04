# Makefile for trufflehog-local-git-repos.sh
# Provides targets to check for and install trufflehog

.PHONY: help check install clean test

# Detect OS and architecture
UNAME_S := $(shell uname -s 2>/dev/null || echo "Linux")
UNAME_M := $(shell uname -m 2>/dev/null || echo "amd64")

# Map uname output to trufflehog release names
ifeq ($(UNAME_S),Linux)
	OS := linux
else ifeq ($(UNAME_S),Darwin)
	OS := darwin
else ifeq ($(UNAME_S),MINGW32_NT-6.1)
	OS := windows
else ifeq ($(UNAME_S),MINGW64_NT-6.1)
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

# Installation directory (defaults to ~/bin, creates it if needed)
# On Linux, always use user's home directory to avoid requiring sudo
HOME_DIR := $(shell echo $$HOME)
INSTALL_DIR := $(HOME_DIR)/bin
# Default version (will fetch latest during install if curl/jq available)
TRUFFLEHOG_VERSION := v3.91.2

help:
	@echo "Trufflehog Local Git Repos - Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  make check     - Check if trufflehog is installed"
	@echo "  make install   - Install trufflehog binary"
	@echo "  make clean     - Remove downloaded trufflehog files"
	@echo "  make test      - Test the script (requires trufflehog)"
	@echo ""
	@echo "Detected OS: $(OS)"
	@echo "Detected Arch: $(ARCH)"
	@echo "Install directory: $(INSTALL_DIR)"
	@echo "Trufflehog version: $(TRUFFLEHOG_VERSION)"

check:
	@echo "Checking for trufflehog..."
	@if command -v trufflehog >/dev/null 2>&1; then \
		echo "✓ trufflehog is installed: $$(which trufflehog)"; \
		trufflehog --version 2>/dev/null || echo "  (version check failed)"; \
	else \
		echo "✗ trufflehog is not installed"; \
		echo "  Run 'make install' to install it"; \
		exit 1; \
	fi

install: check-install-dir
	@VERSION="$(TRUFFLEHOG_VERSION)"; \
	if command -v jq >/dev/null 2>&1; then \
		LATEST=$$(curl -s https://api.github.com/repos/trufflesecurity/trufflehog/releases/latest 2>/dev/null | jq -r '.tag_name' 2>/dev/null); \
		if [ -n "$$LATEST" ] && [ "$$LATEST" != "null" ]; then \
			VERSION="$$LATEST"; \
		fi; \
	fi; \
	echo "Installing trufflehog $$VERSION for $(OS)/$(ARCH)..."; \
	echo "Install directory: $(INSTALL_DIR)"; \
	if command -v trufflehog >/dev/null 2>&1; then \
		echo "trufflehog is already installed: $$(which trufflehog)"; \
		exit 0; \
	fi; \
	mkdir -p "$(INSTALL_DIR)" || { \
		echo "ERROR: Cannot create directory $(INSTALL_DIR)"; \
		exit 1; \
	}; \
	mkdir -p /tmp/trufflehog-install; \
	cd /tmp/trufflehog-install && \
		curl -L -o trufflehog.tar.gz "https://github.com/trufflesecurity/trufflehog/releases/download/$$VERSION/trufflehog_$${VERSION#v}_$(OS)_$(ARCH).tar.gz" && \
		tar -xzf trufflehog.tar.gz && \
		chmod +x trufflehog && \
		mv trufflehog "$(INSTALL_DIR)/trufflehog" && \
		echo "✓ Installed trufflehog to $(INSTALL_DIR)/trufflehog"; \
	rm -rf /tmp/trufflehog-install; \
	echo ""; \
	echo "Note: Make sure $(INSTALL_DIR) is in your PATH"; \
	echo "Add this to your ~/.bashrc or ~/.zshrc:"; \
	echo "  export PATH=\"$$HOME/bin:\$$PATH\""

check-install-dir:
	@# Create install directory if it doesn't exist
	@if [ ! -d "$(INSTALL_DIR)" ]; then \
		mkdir -p "$(INSTALL_DIR)" 2>/dev/null || { \
			echo "ERROR: Cannot create directory $(INSTALL_DIR)"; \
			echo "Please check permissions or choose a different install directory:"; \
			echo "  INSTALL_DIR=/path/to/dir make install"; \
			exit 1; \
		}; \
	fi
	@# Check if we can write to the directory
	@if [ ! -w "$(INSTALL_DIR)" ]; then \
		echo "ERROR: Cannot write to $(INSTALL_DIR)"; \
		echo "Please check permissions or choose a different install directory:"; \
		echo "  INSTALL_DIR=/path/to/dir make install"; \
		exit 1; \
	fi

clean:
	@echo "Cleaning up temporary files..."
	@rm -rf /tmp/trufflehog-install
	@echo "✓ Cleanup complete"

test: check
	@echo "Testing trufflehog-local-git-repos.sh..."
	@if [ ! -f "./trufflehog-local-git-repos.sh" ]; then \
		echo "ERROR: trufflehog-local-git-repos.sh not found"; \
		exit 1; \
	fi
	@bash -n ./trufflehog-local-git-repos.sh && echo "✓ Syntax check passed" || exit 1
	@./trufflehog-local-git-repos.sh -h >/dev/null && echo "✓ Help output works" || exit 1
	@echo "✓ All tests passed"
