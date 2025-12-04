# Recommendation: Externalizing SSH Key Filenames

## Current Problem

SSH key filenames were previously hardcoded in test files and documentation (now replaced with placeholders):
- `your-key-no-passphrase.pem` (example: key without passphrase)
- `your-key-with-passphrase` (example: key with passphrase)
- `your-second-key` (example: additional test key)
- `your-third-key` (example: additional test key)

These appear in:
- Archive test scripts (`test-k-option-*.sh`)
- Archive documentation (`TESTING-PLAN-load-ssh-key-k-option.md`)
- Unit test comments (`test_kill_option.bats`)
- Tips and tricks documentation

## Recommended Solution: Gitignored Config File

**Approach**: Create a simple configuration file that's gitignored, allowing each user to define their own test keys.

### Option 1: Project-Level Config (Recommended)

**Location**: `tests/load-ssh-key/.test-keys.conf` (gitignored)

**Format** (simple key-value pairs):
```bash
# SSH Key Configuration for Tests
# This file is gitignored - customize with your own key names

# Key without passphrase (for basic tests)
TEST_KEY_NO_PASSPHRASE="your-key-no-passphrase.pem"

# Key with passphrase (for passphrase tests)
TEST_KEY_WITH_PASSPHRASE="your-key-with-passphrase"

# Additional test keys (optional)
TEST_KEY_2="your-second-key"
TEST_KEY_3="your-third-key"
```

**Usage in scripts**:
```bash
# Load config (required - no defaults)
CONFIG_FILE="${SCRIPT_DIR}/tests/load-ssh-key/.test-keys.conf"
if [ ! -f "${CONFIG_FILE}" ]; then
    echo "ERROR: Test key configuration file not found: ${CONFIG_FILE}" >&2
    echo "Please run: ./tests/load-ssh-key/setup-test-keys-config.sh" >&2
    echo "Or create it from .test-keys.conf.example" >&2
    exit 1
fi
source "${CONFIG_FILE}"

# Verify required variables are set
if [ -z "${TEST_KEY_NO_PASSPHRASE:-}" ] || [ -z "${TEST_KEY_WITH_PASSPHRASE:-}" ]; then
    echo "ERROR: Required test key variables not set in config file" >&2
    exit 1
fi
```

**Pros**:
- ✅ Simple key-value format
- ✅ Project-specific (stays with repo)
- ✅ Gitignored (won't be committed)
- ✅ Easy to document with example file
- ✅ No hardcoded key names in git

**Cons**:
- ⚠️ Requires file to exist (must be created from example)

**Setup Helper Script**: `tests/load-ssh-key/setup-test-keys-config.sh`
```bash
#!/usr/bin/env bash
# Setup helper for creating .test-keys.conf

set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/.test-keys.conf"
EXAMPLE_FILE="${SCRIPT_DIR}/.test-keys.conf.example"

cat<<EOF
================================================================================
SSH Test Key Configuration Setup
================================================================================
This script will help you create a test key configuration file.
The file will be stored at: ${CONFIG_FILE}
================================================================================
EOF

# Check if config already exists
if [ -f "${CONFIG_FILE}" ]; then
    cat<<EOF
WARNING: ${CONFIG_FILE} already exists.
Do you want to overwrite it? (y/N)
EOF
    read response
    if [ "${response}" != "y" ] && [ "${response}" != "Y" ]; then
        echo "Exiting without changes."
        exit 0
    fi
    echo "Loading existing values to use as defaults..."
    set +u
    source "${CONFIG_FILE}" 2>/dev/null || true
    EXISTING_KEY_NO_PASS="${TEST_KEY_NO_PASSPHRASE:-}"
    EXISTING_KEY_WITH_PASS="${TEST_KEY_WITH_PASSPHRASE:-}"
    set -u
fi

echo ""
echo "Enter the name of your SSH key WITHOUT passphrase (for basic tests):"
if [ -n "${EXISTING_KEY_NO_PASS:-}" ]; then
    echo "(current: ${EXISTING_KEY_NO_PASS})"
fi
read -r TEST_KEY_NO_PASSPHRASE
if [ -z "${TEST_KEY_NO_PASSPHRASE}" ] && [ -n "${EXISTING_KEY_NO_PASS:-}" ]; then
    TEST_KEY_NO_PASSPHRASE="${EXISTING_KEY_NO_PASS}"
fi

echo ""
echo "Enter the name of your SSH key WITH passphrase (for passphrase tests):"
if [ -n "${EXISTING_KEY_WITH_PASS:-}" ]; then
    echo "(current: ${EXISTING_KEY_WITH_PASS})"
fi
read -r TEST_KEY_WITH_PASSPHRASE
if [ -z "${TEST_KEY_WITH_PASSPHRASE}" ] && [ -n "${EXISTING_KEY_WITH_PASS:-}" ]; then
    TEST_KEY_WITH_PASSPHRASE="${EXISTING_KEY_WITH_PASS}"
fi

# Validate
if [ -z "${TEST_KEY_NO_PASSPHRASE}" ] || [ -z "${TEST_KEY_WITH_PASSPHRASE}" ]; then
    echo "ERROR: Both keys are required"
    exit 1
fi

# Write config file
cat > "${CONFIG_FILE}" <<EOF
# SSH Key Configuration for Tests
# This file is gitignored - customize with your own key names

# Key without passphrase (for basic tests)
TEST_KEY_NO_PASSPHRASE="${TEST_KEY_NO_PASSPHRASE}"

# Key with passphrase (for passphrase tests)
TEST_KEY_WITH_PASSPHRASE="${TEST_KEY_WITH_PASSPHRASE}"

# Additional test keys (optional)
# TEST_KEY_2="your-second-key"
# TEST_KEY_3="your-third-key"
EOF

echo ""
echo "Configuration file created: ${CONFIG_FILE}"
echo "You can now run the tests."
```

---

### Option 2: User Home Directory Config

**Location**: `~/.ssh/test-keys.conf` or `~/.config/load-ssh-key-test-keys.conf`

**Format**: Same as Option 1

**Usage**:
```bash
# Try multiple locations (required - no defaults)
CONFIG_FILE="${HOME}/.ssh/test-keys.conf"
[ -f "${CONFIG_FILE}" ] || CONFIG_FILE="${HOME}/.config/load-ssh-key-test-keys.conf"

if [ ! -f "${CONFIG_FILE}" ]; then
    echo "ERROR: Test key configuration file not found" >&2
    echo "Please run: ./tests/load-ssh-key/setup-test-keys-home.sh" >&2
    echo "Or create ${HOME}/.ssh/test-keys.conf or ${HOME}/.config/load-ssh-key-test-keys.conf" >&2
    exit 1
fi
source "${CONFIG_FILE}"

# Verify required variables are set
if [ -z "${TEST_KEY_NO_PASSPHRASE:-}" ] || [ -z "${TEST_KEY_WITH_PASSPHRASE:-}" ]; then
    echo "ERROR: Required test key variables not set in config file" >&2
    exit 1
fi
```

**Pros**:
- ✅ User-specific (works across projects)
- ✅ Near SSH keys (logical location)
- ✅ No hardcoded key names in git

**Cons**:
- ⚠️ Less discoverable
- ⚠️ Multiple possible locations
- ⚠️ Requires file to exist (must be created)

**Setup Helper Script**: `tests/load-ssh-key/setup-test-keys-home.sh`
```bash
#!/usr/bin/env bash
# Setup helper for creating test keys config in home directory

set -eu

CONFIG_FILE="${HOME}/.ssh/test-keys.conf"
ALT_CONFIG_FILE="${HOME}/.config/load-ssh-key-test-keys.conf"

cat<<EOF
================================================================================
SSH Test Key Configuration Setup
================================================================================
This script will help you create a test key configuration file.
Preferred location: ${CONFIG_FILE}
Alternative location: ${ALT_CONFIG_FILE}
================================================================================
EOF

# Check if config already exists
if [ -f "${CONFIG_FILE}" ]; then
    EXISTING_FILE="${CONFIG_FILE}"
elif [ -f "${ALT_CONFIG_FILE}" ]; then
    EXISTING_FILE="${ALT_CONFIG_FILE}"
else
    EXISTING_FILE=""
fi

if [ -n "${EXISTING_FILE}" ]; then
    cat<<EOF
WARNING: ${EXISTING_FILE} already exists.
Do you want to overwrite it? (y/N)
EOF
    read response
    if [ "${response}" != "y" ] && [ "${response}" != "Y" ]; then
        echo "Exiting without changes."
        exit 0
    fi
    echo "Loading existing values to use as defaults..."
    set +u
    source "${EXISTING_FILE}" 2>/dev/null || true
    EXISTING_KEY_NO_PASS="${TEST_KEY_NO_PASSPHRASE:-}"
    EXISTING_KEY_WITH_PASS="${TEST_KEY_WITH_PASSPHRASE:-}"
    set -u
fi

echo ""
echo "Enter the name of your SSH key WITHOUT passphrase (for basic tests):"
if [ -n "${EXISTING_KEY_NO_PASS:-}" ]; then
    echo "(current: ${EXISTING_KEY_NO_PASS})"
fi
read -r TEST_KEY_NO_PASSPHRASE
if [ -z "${TEST_KEY_NO_PASSPHRASE}" ] && [ -n "${EXISTING_KEY_NO_PASS:-}" ]; then
    TEST_KEY_NO_PASSPHRASE="${EXISTING_KEY_NO_PASS}"
fi

echo ""
echo "Enter the name of your SSH key WITH passphrase (for passphrase tests):"
if [ -n "${EXISTING_KEY_WITH_PASS:-}" ]; then
    echo "(current: ${EXISTING_KEY_WITH_PASS})"
fi
read -r TEST_KEY_WITH_PASSPHRASE
if [ -z "${TEST_KEY_WITH_PASSPHRASE}" ] && [ -n "${EXISTING_KEY_WITH_PASS:-}" ]; then
    TEST_KEY_WITH_PASSPHRASE="${EXISTING_KEY_WITH_PASS}"
fi

# Validate
if [ -z "${TEST_KEY_NO_PASSPHRASE}" ] || [ -z "${TEST_KEY_WITH_PASSPHRASE}" ]; then
    echo "ERROR: Both keys are required"
    exit 1
fi

# Choose location
echo ""
echo "Choose location:"
echo "1) ${CONFIG_FILE} (recommended)"
echo "2) ${ALT_CONFIG_FILE}"
read -r choice

if [ "${choice}" = "2" ]; then
    CONFIG_FILE="${ALT_CONFIG_FILE}"
    mkdir -p "$(dirname "${CONFIG_FILE}")"
fi

# Write config file
cat > "${CONFIG_FILE}" <<EOF
# SSH Key Configuration for Tests
# This file is user-specific and works across projects

# Key without passphrase (for basic tests)
TEST_KEY_NO_PASSPHRASE="${TEST_KEY_NO_PASSPHRASE}"

# Key with passphrase (for passphrase tests)
TEST_KEY_WITH_PASSPHRASE="${TEST_KEY_WITH_PASSPHRASE}"

# Additional test keys (optional)
# TEST_KEY_2="your-second-key"
# TEST_KEY_3="your-third-key"
EOF

echo ""
echo "Configuration file created: ${CONFIG_FILE}"
echo "You can now run the tests."
```

---

### Option 3: Environment Variables (Simplest)

**Approach**: Use environment variables with sensible defaults

**Usage**:
```bash
# Verify required environment variables are set (no defaults)
if [ -z "${TEST_KEY_NO_PASSPHRASE:-}" ] || [ -z "${TEST_KEY_WITH_PASSPHRASE:-}" ]; then
    echo "ERROR: Required test key environment variables not set" >&2
    echo "Please run: ./tests/load-ssh-key/setup-test-keys-env.sh" >&2
    echo "Or set TEST_KEY_NO_PASSPHRASE and TEST_KEY_WITH_PASSPHRASE" >&2
    exit 1
fi
```

**User setup** (in `~/.bashrc` or `~/.zshrc`):
```bash
export TEST_KEY_NO_PASSPHRASE="my-key.pem"
export TEST_KEY_WITH_PASSPHRASE="my-key-with-pass"
```

**Setup Helper Script**: `tests/load-ssh-key/setup-test-keys-env.sh`
```bash
#!/usr/bin/env bash
# Setup helper for setting test key environment variables

set -eu

cat<<EOF
================================================================================
SSH Test Key Environment Variable Setup
================================================================================
This script will help you set up environment variables for test keys.
You can add these to your ~/.bashrc or ~/.zshrc file.
================================================================================
EOF

echo ""
echo "Enter the name of your SSH key WITHOUT passphrase (for basic tests):"
read -r TEST_KEY_NO_PASSPHRASE

echo ""
echo "Enter the name of your SSH key WITH passphrase (for passphrase tests):"
read -r TEST_KEY_WITH_PASSPHRASE

# Validate
if [ -z "${TEST_KEY_NO_PASSPHRASE}" ] || [ -z "${TEST_KEY_WITH_PASSPHRASE}" ]; then
    echo "ERROR: Both keys are required"
    exit 1
fi

# Detect shell config file
if [ -f "${HOME}/.zshrc" ]; then
    SHELL_CONFIG="${HOME}/.zshrc"
elif [ -f "${HOME}/.bashrc" ]; then
    SHELL_CONFIG="${HOME}/.bashrc"
else
    SHELL_CONFIG="${HOME}/.bashrc"
fi

cat<<EOF

Add these lines to ${SHELL_CONFIG}:

export TEST_KEY_NO_PASSPHRASE="${TEST_KEY_NO_PASSPHRASE}"
export TEST_KEY_WITH_PASSPHRASE="${TEST_KEY_WITH_PASSPHRASE}"

Would you like me to append these to ${SHELL_CONFIG}? (y/N)
EOF
read response

if [ "${response}" = "y" ] || [ "${response}" = "Y" ]; then
    {
        echo ""
        echo "# SSH Test Key Configuration (added by setup-test-keys-env.sh)"
        echo "export TEST_KEY_NO_PASSPHRASE=\"${TEST_KEY_NO_PASSPHRASE}\""
        echo "export TEST_KEY_WITH_PASSPHRASE=\"${TEST_KEY_WITH_PASSPHRASE}\""
    } >> "${SHELL_CONFIG}"
    echo ""
    echo "Configuration added to ${SHELL_CONFIG}"
    echo "Please run: source ${SHELL_CONFIG}"
    echo "Or restart your terminal."
else
    echo ""
    echo "Please manually add the export statements to your shell config file."
fi
```

**Pros**:
- ✅ Simplest implementation
- ✅ No files needed
- ✅ No hardcoded key names in git

**Cons**:
- ⚠️ Must be set (no defaults)
- ⚠️ Less discoverable
- ⚠️ Environment pollution
- ⚠️ Easy to forget to set

---

### Option 4: Secure Directory Pattern (From create-set-api-key.sh)

**Location**: `${HOME}/.secure/load-ssh-key-test-keys.sh`

**Approach**: Store configuration in a secure directory (`~/.secure/`) with restrictive permissions, similar to how `create-set-api-key.sh` handles API keys.

**Format** (bash script that exports variables):
```bash
# SSH Key Configuration for Tests
# This file is in ~/.secure/ with restricted permissions

export TEST_KEY_NO_PASSPHRASE="your-key-no-passphrase.pem"
export TEST_KEY_WITH_PASSPHRASE="your-key-with-passphrase"
export TEST_KEY_2="your-second-key"
export TEST_KEY_3="your-third-key"
```

**Usage**:
```bash
# Define secure directory
SECURE_DIR="${HOME}/.secure"
CONFIG_FILE="${SECURE_DIR}/load-ssh-key-test-keys.sh"

# Create secure directory if it doesn't exist
if [ ! -d "${SECURE_DIR}" ]; then
    mkdir -p "${SECURE_DIR}"
    chmod 700 "${SECURE_DIR}"
fi

# Load config (required - no defaults)
if [ ! -f "${CONFIG_FILE}" ]; then
    echo "ERROR: Test key configuration file not found: ${CONFIG_FILE}" >&2
    echo "Please run: ./tests/load-ssh-key/archive/setup-test-keys-secure.sh" >&2
    echo "Or create it manually in ${SECURE_DIR}/" >&2
    exit 1
fi

# Temporarily disable set -u to safely source
set +u
source "${CONFIG_FILE}" 2>/dev/null || {
    echo "ERROR: Failed to load config file: ${CONFIG_FILE}" >&2
    set -u
    exit 1
}
set -u

# Verify required variables are set
if [ -z "${TEST_KEY_NO_PASSPHRASE:-}" ] || [ -z "${TEST_KEY_WITH_PASSPHRASE:-}" ]; then
    echo "ERROR: Required test key variables not set in config file" >&2
    exit 1
fi
```

**Setup Helper Script**: `tests/load-ssh-key/archive/setup-test-keys-secure.sh`
```bash
#!/usr/bin/env bash
# Setup helper for creating test keys config in secure directory
# Follows the pattern from create-set-api-key.sh

set -eu

SECURE_DIR="${HOME}/.secure"
CONFIG_FILE="${SECURE_DIR}/load-ssh-key-test-keys.sh"

cat<<EOF
================================================================================
SSH Test Key Configuration Setup (Secure Directory)
================================================================================
This script will help you create a test key configuration file in a secure
directory with restrictive permissions, following the pattern from
create-set-api-key.sh.

The configuration will be stored in: ${CONFIG_FILE}
================================================================================
EOF

# Create secure directory if it doesn't exist
if [ ! -d "${SECURE_DIR}" ]; then
    echo "Creating secure directory: ${SECURE_DIR}"
    mkdir -p "${SECURE_DIR}"
    chmod 700 "${SECURE_DIR}"
fi

# Check if config already exists
if [ -f "${CONFIG_FILE}" ]; then
    cat<<EOF
WARNING: ${CONFIG_FILE} already exists.
Do you want to overwrite it? (y/N)
EOF
    read response
    if [ "${response}" != "y" ] && [ "${response}" != "Y" ]; then
        echo "Exiting without changes."
        exit 0
    fi
    echo "Loading existing values to use as defaults..."
    set +u
    source "${CONFIG_FILE}" 2>/dev/null || true
    EXISTING_KEY_NO_PASS="${TEST_KEY_NO_PASSPHRASE:-}"
    EXISTING_KEY_WITH_PASS="${TEST_KEY_WITH_PASSPHRASE:-}"
    set -u
fi

cat<<EOF
Go get your SSH key names from ${HOME}/.ssh/
Press Enter to continue.
EOF
read continue

echo ""
echo "Enter the name of your SSH key WITHOUT passphrase (for basic tests):"
if [ -n "${EXISTING_KEY_NO_PASS:-}" ]; then
    echo "(current: ${EXISTING_KEY_NO_PASS})"
fi
read -r TEST_KEY_NO_PASSPHRASE
if [ -z "${TEST_KEY_NO_PASSPHRASE}" ] && [ -n "${EXISTING_KEY_NO_PASS:-}" ]; then
    TEST_KEY_NO_PASSPHRASE="${EXISTING_KEY_NO_PASS}"
fi

echo ""
echo "Enter the name of your SSH key WITH passphrase (for passphrase tests):"
if [ -n "${EXISTING_KEY_WITH_PASS:-}" ]; then
    echo "(current: ${EXISTING_KEY_WITH_PASS})"
fi
read -r TEST_KEY_WITH_PASSPHRASE
if [ -z "${TEST_KEY_WITH_PASSPHRASE}" ] && [ -n "${EXISTING_KEY_WITH_PASS:-}" ]; then
    TEST_KEY_WITH_PASSPHRASE="${EXISTING_KEY_WITH_PASS}"
fi

# Validate
if [ -z "${TEST_KEY_NO_PASSPHRASE}" ] || [ -z "${TEST_KEY_WITH_PASSPHRASE}" ]; then
    echo "ERROR: Both keys are required"
    exit 1
fi

# Write to temporary file first, then move to final location
# This ensures we don't lose the existing file if something goes wrong
temp_file=$(mktemp "${SECURE_DIR}/load-ssh-key-test-keys.sh.XXXXXX")

cat > "${temp_file}" <<EOF
# SSH Key Configuration for Tests
# This file is in ~/.secure/ with restricted permissions

export TEST_KEY_NO_PASSPHRASE="${TEST_KEY_NO_PASSPHRASE}"
export TEST_KEY_WITH_PASSPHRASE="${TEST_KEY_WITH_PASSPHRASE}"
export TEST_KEY_2="${TEST_KEY_2:-}"
export TEST_KEY_3="${TEST_KEY_3:-}"
EOF

chmod 400 "${temp_file}"

# Move temp file to final location (mv will overwrite even read-only files)
mv -f "${temp_file}" "${CONFIG_FILE}"

cat<<EOF
================================================================================
Configuration file created
set_api_key=[${CONFIG_FILE}]
================================================================================
EOF
ls -lad "${SECURE_DIR}"
ls -la "${CONFIG_FILE}"
```

**Pros**:
- ✅ Secure by default (restrictive permissions)
- ✅ User-specific (works across projects)
- ✅ Follows established pattern (from create-set-api-key.sh)
- ✅ Centralized secure storage location
- ✅ No hardcoded key names in git
- ✅ Can load existing values as defaults (like create-set-api-key.sh does)

**Cons**:
- ⚠️ Requires creating `~/.secure/` directory
- ⚠️ Requires config file to exist (must be created)
- ⚠️ Less discoverable (not in project directory)
- ⚠️ More complex setup (permissions management)

**Key Features from create-set-api-key.sh pattern**:
- Uses `${HOME}/.secure/` directory (chmod 700)
- Config file is a bash script with exports (chmod 400)
- Can source existing config to load previous values as defaults
- Secure by design with restrictive permissions

---

## Recommended Implementation: Required Config (No Defaults)

**Goal**: Completely eliminate hardcoded key names from git-tracked files

1. **Create example config file**: `tests/load-ssh-key/.test-keys.conf.example`
   - Committed to git as a template with placeholder values
   - Users copy to `.test-keys.conf` (gitignored) and customize

2. **Load config (required - no defaults)**:
   ```bash
   # Load from config file (required)
   CONFIG_FILE="${SCRIPT_DIR}/tests/load-ssh-key/.test-keys.conf"
   if [ ! -f "${CONFIG_FILE}" ]; then
       echo "ERROR: Test key configuration file not found: ${CONFIG_FILE}" >&2
       echo "Please create it from .test-keys.conf.example" >&2
       exit 1
   fi
   source "${CONFIG_FILE}"
   
   # Verify required variables are set
   if [ -z "${TEST_KEY_NO_PASSPHRASE:-}" ] || [ -z "${TEST_KEY_WITH_PASSPHRASE:-}" ]; then
       echo "ERROR: Required test key variables not set in config file" >&2
       exit 1
   fi
   ```

3. **Update .gitignore**:
   ```
   tests/load-ssh-key/.test-keys.conf
   ```

4. **Documentation**: Add to README how to set up test keys

**Key principle**: No default values means no key names in git-tracked files

---

## Implementation Steps

1. Create `.test-keys.conf.example` with placeholder values
2. Add `.test-keys.conf` to `.gitignore`
3. Create setup helper scripts for each option:
   - `setup-test-keys-config.sh` (Option 1)
   - `setup-test-keys-home.sh` (Option 2)
   - `setup-test-keys-env.sh` (Option 3)
   - `archive/setup-test-keys-secure.sh` (Option 4 - for archive scripts only)
4. Create helper function to load config
5. Update archive scripts to use config variables
6. Update documentation to reference config and setup scripts
7. Add setup instructions to README

## Setup Scripts Summary

All four options include interactive setup scripts that:
- Walk users through the configuration process
- Load existing values as defaults (if config exists)
- Validate required inputs
- Create config files with proper permissions
- Follow the same pattern as `create-set-api-key.sh`

**Usage**:
```bash
# Option 1: Project-level config
./tests/load-ssh-key/setup-test-keys-config.sh

# Option 2: Home directory config
./tests/load-ssh-key/setup-test-keys-home.sh

# Option 3: Environment variables
./tests/load-ssh-key/setup-test-keys-env.sh

# Option 4: Secure directory
./tests/load-ssh-key/archive/setup-test-keys-secure.sh
```

---

## Example Helper Function

```bash
# Load test key configuration (required - no defaults)
load_test_key_config() {
    local config_file="${SCRIPT_DIR}/tests/load-ssh-key/.test-keys.conf"
    
    # Load config file (required)
    if [ ! -f "${config_file}" ]; then
        echo "ERROR: Test key configuration file not found: ${config_file}" >&2
        echo "Please create it from .test-keys.conf.example" >&2
        return 1
    fi
    
    source "${config_file}" || {
        echo "ERROR: Failed to load config file: ${config_file}" >&2
        return 1
    }
    
    # Verify required variables are set
    if [ -z "${TEST_KEY_NO_PASSPHRASE:-}" ] || [ -z "${TEST_KEY_WITH_PASSPHRASE:-}" ]; then
        echo "ERROR: Required test key variables not set in config file" >&2
        echo "Required: TEST_KEY_NO_PASSPHRASE, TEST_KEY_WITH_PASSPHRASE" >&2
        return 1
    fi
    
    # Export for use in scripts
    export TEST_KEY_NO_PASSPHRASE
    export TEST_KEY_WITH_PASSPHRASE
    export TEST_KEY_2="${TEST_KEY_2:-}"
    export TEST_KEY_3="${TEST_KEY_3:-}"
}
```

---

## Recommendation Summary

### For Most Users: Option 1 (Project-Level Config)
**Use Option 1 (Project-Level Config) - Required config, no defaults**:
- ✅ Simple and straightforward
- ✅ Discoverable (in project directory)
- ✅ Safe (gitignored, won't leak keys)
- ✅ Easy to document
- ✅ **No key names in git-tracked files**
- ✅ **Interactive setup script available** (`setup-test-keys-config.sh`)

This approach provides the best balance of simplicity, discoverability, and ensures no hardcoded key names remain in git.

### For Security-Conscious Users: Option 4 (Secure Directory)
**Use Option 4 (Secure Directory Pattern) if**:
- You want maximum security with restrictive permissions
- You prefer centralized secure storage
- You want to follow the established pattern from `create-set-api-key.sh`
- You're comfortable with more complex setup
- ✅ **No key names in git-tracked files**
- ✅ **Interactive setup script available** (`archive/setup-test-keys-secure.sh` - for archive scripts only)

**Comparison**:
- Option 1: Easier setup, project-specific, good for most cases
- Option 4: More secure, user-wide, follows security best practices

**Important**: 
- All options require configuration - no default values means no key names in git-tracked files
- All options include interactive setup scripts that walk users through the configuration process, similar to `create-set-api-key.sh`
