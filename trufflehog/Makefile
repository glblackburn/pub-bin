# Makefile for trufflehog-local-git-repos.sh
# Provides targets to check for and install trufflehog
# Pattern follows: /Users/lblackb/data/lblackb/git/make-templates/make/Makefile_software.mk

.PHONY: help trufflehog install-trufflehog check clean test uninstall update install-deps check-deps

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
	@echo "Trufflehog Scripts - Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  make trufflehog        - Install trufflehog (alias for install-trufflehog)"
	@echo "  make install-trufflehog - Install trufflehog binary"
	@echo "  make install-deps      - Install Python dependencies (GitPython, PyGithub)"
	@echo "  make check             - Check if trufflehog is installed"
	@echo "  make check-deps        - Check if Python dependencies are installed"
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
	@echo "  make install-deps                  # Install Python dependencies"
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
	export INSTALL_VERSION="$$VERSION"; \
	$(MAKE) do-install VERSION="$$INSTALL_VERSION"

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
	UPDATE_VERSION="$$VERSION"; \
	$(MAKE) do-install VERSION="$$UPDATE_VERSION" FORCE=1

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
	@if [ ! -f "./scripts/trufflehog-local-git-repos.sh" ]; then \
		echo "ERROR: trufflehog-local-git-repos.sh not found"; \
		exit 1; \
	fi
	@bash -n ./scripts/trufflehog-local-git-repos.sh && echo "✓ Syntax check passed" || exit 1
	@./scripts/trufflehog-local-git-repos.sh -h >/dev/null && echo "✓ Help output works" || exit 1
	@echo "✓ All tests passed"

check-deps: ## check if Python dependencies are installed
	@echo "Checking for Python dependencies..."
	@if ! command -v python3 >/dev/null 2>&1; then \
		echo "✗ python3 is not installed"; \
		echo "  Install Python 3.8+ to use Python scripts"; \
		exit 1; \
	fi
	@PYTHON_VERSION=$$(python3 --version 2>&1 | awk '{print $$2}'); \
	echo "✓ Python version: $$PYTHON_VERSION"; \
	DEPS_MISSING=0; \
	if python3 -c "import git" 2>/dev/null; then \
		GITPYTHON_VERSION=$$(python3 -c "import git; print(git.__version__)" 2>/dev/null || echo "unknown"); \
		echo "✓ GitPython is installed (version: $$GITPYTHON_VERSION)"; \
	else \
		echo "✗ GitPython is not installed"; \
		DEPS_MISSING=1; \
	fi; \
	if python3 -c "import github" 2>/dev/null; then \
		PYGITHUB_VERSION=$$(python3 -c "import github; print(github.__version__)" 2>/dev/null || echo "unknown"); \
		echo "✓ PyGithub is installed (version: $$PYGITHUB_VERSION)"; \
	else \
		echo "✗ PyGithub is not installed (optional - needed for PR creation via API)"; \
		DEPS_MISSING=1; \
	fi; \
	if command -v gh >/dev/null 2>&1; then \
		GH_VERSION=$$(gh --version 2>/dev/null | head -1 || echo "unknown"); \
		echo "✓ GitHub CLI (gh) is installed: $$GH_VERSION"; \
	else \
		echo "⚠ GitHub CLI (gh) is not installed (optional - recommended for PR creation)"; \
	fi; \
	if [ $$DEPS_MISSING -eq 1 ]; then \
		echo ""; \
		echo "Run 'make install-deps' to install missing dependencies"; \
		exit 1; \
	fi

install-deps: ## install Python dependencies
	@echo "Installing Python dependencies..."
	@if ! command -v python3 >/dev/null 2>&1; then \
		echo "ERROR: python3 is not installed"; \
		echo "  Install Python 3.8+ first"; \
		exit 1; \
	fi
	@PYTHON_VERSION=$$(python3 --version 2>&1 | awk '{print $$2}'); \
	echo "Python version: $$PYTHON_VERSION"; \
	INSTALLED_ANY=0; \
	\
	# Install GitPython \
	if python3 -c "import git" 2>/dev/null; then \
		GITPYTHON_VERSION=$$(python3 -c "import git; print(git.__version__)" 2>/dev/null || echo "unknown"); \
		echo "✓ GitPython is already installed (version: $$GITPYTHON_VERSION)"; \
	else \
		echo "Installing GitPython..."; \
		if python3 -m pip install --user "GitPython>=3.1.0"; then \
			echo "✓ GitPython installed successfully"; \
			INSTALLED_ANY=1; \
		else \
			echo "ERROR: Failed to install GitPython"; \
			echo "  Try: pip3 install GitPython"; \
			exit 1; \
		fi; \
	fi; \
	\
	# Install PyGithub (optional, for PR creation via API) \
	if python3 -c "import github" 2>/dev/null; then \
		PYGITHUB_VERSION=$$(python3 -c "import github; print(github.__version__)" 2>/dev/null || echo "unknown"); \
		echo "✓ PyGithub is already installed (version: $$PYGITHUB_VERSION)"; \
	else \
		echo "Installing PyGithub (for PR creation via API)..."; \
		if python3 -m pip install --user "PyGithub>=2.0.0"; then \
			echo "✓ PyGithub installed successfully"; \
			INSTALLED_ANY=1; \
		else \
			echo "WARNING: Failed to install PyGithub"; \
			echo "  PR creation will require GitHub CLI (gh) instead"; \
			echo "  Try: pip3 install PyGithub"; \
		fi; \
	fi; \
	\
	if [ $$INSTALLED_ANY -eq 1 ]; then \
		echo ""; \
		echo "Note: If you get 'command not found' errors, ensure pip's user bin directory is in your PATH:"; \
		PIP_USER_BIN=$$(python3 -m site --user-base)/bin; \
		echo "  export PATH=\"$$PIP_USER_BIN:\$$PATH\""; \
	fi; \
	\
	# Check for GitHub CLI \
	if command -v gh >/dev/null 2>&1; then \
		GH_VERSION=$$(gh --version 2>/dev/null | head -1 || echo "unknown"); \
		echo ""; \
		echo "✓ GitHub CLI (gh) is installed: $$GH_VERSION"; \
		echo "  Run 'gh auth login' to authenticate for PR creation"; \
	else \
		echo ""; \
		echo "⚠ GitHub CLI (gh) is not installed (recommended for PR creation)"; \
		echo "  Install with: brew install gh  # macOS"; \
		echo "  Or download from: https://cli.github.com/"; \
	fi

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
	VERSION_VAL="$(VERSION)"; \
	mkdir -p "$(INSTALL_DIR)" || { \
		echo "ERROR: Cannot create directory $(INSTALL_DIR)"; \
		exit 1; \
	}; \
	TMP_DIR=$$(mktemp -d) || { \
		echo "ERROR: Cannot create temporary directory"; \
		exit 1; \
	}; \
	trap "rm -rf $$TMP_DIR" EXIT; \
	echo "Downloading trufflehog $$VERSION_VAL..."; \
	VERSION_NO_V=$${VERSION_VAL#v}; \
	FILENAME="trufflehog_$${VERSION_NO_V}_$(OS)_$(ARCH).tar.gz"; \
	DOWNLOAD_URL="https://github.com/trufflesecurity/trufflehog/releases/download/$$VERSION_VAL/$$FILENAME"; \
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
