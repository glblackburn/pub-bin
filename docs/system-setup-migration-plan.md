# System Setup Scripts Migration Plan

Analysis and recommendations for migrating scripts from `/Users/lblackb/data/lblackb/git/bin/system-setup` to `pub-bin`.

## Analysis Summary

### Current Structure (`system-setup/`)

**Main Scripts:**
- **`setup-system.sh`** - Main orchestrator script that coordinates all setup steps
- **`software-installs.sh`** - Runs all software install scripts in sequence
- **`create-key.sh`** - Creates SSH keys with good default values
- **`setup-bin-config.sh`** - Sets up bin config (references old bin-config system)
- **`setup-remote-syslogd.sh`** - Configures macOS remote syslog daemon (see [analysis](system-setup-remote-syslogd-analysis.md))

**Software Install Scripts (11 total):**
- `01-homebrew.sh` - Homebrew installation check
- `caffeine.sh` - Caffeine app install
- `chrome.sh` - Google Chrome install
- `emacs.sh` - Emacs install
- `gimp.sh` - GIMP install
- `ispell.sh` - Ispell install
- `iterm2.sh` - iTerm2 install
- `keepassxc.sh` - KeePassXC install
- `owasp-zap.sh` - OWASP ZAP install
- `slack.sh` - Slack install
- `NO-keepass.sh`, `NO-veracrypt.sh` - Skipped installs (prefixed with NO-)

**User Configs:**
- `user-configs/bash_profile` - Bash profile template
- `user-configs/emacs` - Emacs configuration template

### Key Observations

**Strengths:**
- ✅ Good error handling (`set -euET -o pipefail`)
- ✅ Modular design (separate install scripts)
- ✅ Interactive prompts for user guidance
- ✅ Skip logic for existing installations

**Issues:**
1. ❌ Hardcoded paths (`${HOME}/data`, GitHub URLs with personal usernames - see sensitive info file)
2. ❌ References old bin-config system (not pub-bin's config system)
3. ❌ macOS-specific assumptions (KeePassX path, Chrome path, syslog config)
4. ❌ User configs contain personal/specific paths (see sensitive info file)
5. ❌ No documentation beyond minimal README
6. ❌ Inconsistent script patterns (some use `#!/bin/bash`, others `#!/usr/bin/env bash`)

## Migration Recommendations

### 1. Organization Structure

Create a new `system-setup/` directory in pub-bin:

```
pub-bin/
├── system-setup/
│   ├── README.md                    # Comprehensive documentation
│   ├── setup-system.sh              # Main orchestrator
│   ├── software-installs.sh         # Software installer runner
│   ├── create-ssh-key.sh            # SSH key creation (rename from create-key.sh)
│   ├── setup-remote-syslogd.sh      # macOS syslog configuration
│   ├── software-installs/
│   │   ├── 01-homebrew.sh
│   │   ├── emacs.sh
│   │   ├── slack.sh
│   │   └── ... (other install scripts)
│   └── templates/
│       ├── bash_profile.template    # Template (not personal config)
│       └── emacs.template            # Template (not personal config)
```

### 2. Script Updates Required

#### A. `setup-system.sh` - Major Refactoring

**Current Issues:**
- Hardcoded `data_dir="${HOME}/data"`
- Hardcoded `bin_git_url` with personal GitHub username (see sensitive info file)
- References old bin-config system
- Hardcoded KeePassX path
- No CLI options

**Required Changes:**
- Replace hardcoded `data_dir` with config system
- Replace `bin_git_url` with pub-bin's config system
- Use `config/config.sh` instead of old bin-config
- Make KeePassX path configurable (or detect automatically)
- Add CLI options for customization (`-h`, `-v`, `-q`)
- Add dry-run mode (`-n`)
- Document all steps in README

#### B. `create-key.sh` → `create-ssh-key.sh`

**Current Status:**
- Already follows good patterns
- Good CLI option handling
- Proper error handling

**Required Changes:**
- Minor: ensure consistent shebang (`#!/usr/bin/env bash`)
- Consider adding to pub-bin root if it's a standalone utility
- Or keep in system-setup if it's only used during setup

#### C. `software-installs.sh`

**Current Status:**
- Already good pattern (iterates through install scripts)
- Handles NO- prefix for skipping

**Required Changes:**
- Ensure all install scripts follow shell-template.sh patterns
- Add error tracking and reporting
- Add summary at end (what installed, what failed, what skipped)

#### D. `setup-bin-config.sh`

**Current Status:**
- References old bin-config system which doesn't exist in pub-bin

**Required Changes:**
- Remove or replace with pub-bin's `config/config.sh` integration
- This script may not be needed if using pub-bin's config system

#### E. `setup-remote-syslogd.sh`

**Current Status:**
- Configures macOS syslogd to listen on network socket (UDP port 514)
- Enables remote syslog message reception
- See [detailed analysis](system-setup-remote-syslogd-analysis.md) for complete assessment

**Required Changes:**
- Make script idempotent (currently fails on second run)
- Add error handling and validation
- Add user feedback and security warnings
- Follow pub-bin script patterns
- Document security implications (opens UDP port 514 to network)

**Note:** This script has significant issues that need to be addressed. See the [analysis document](system-setup-remote-syslogd-analysis.md) for detailed recommendations.

#### F. Individual Software Install Scripts

**Current Status:**
- Some use `#!/bin/bash`, others `#!/usr/bin/env bash`
- Inconsistent patterns

**Required Changes:**
- Standardize shebang to `#!/usr/bin/env bash`
- Ensure all use `set -euET -o pipefail`
- Add consistent error handling
- Consider adding `-h` help option to each
- Follow shell-template.sh patterns

#### G. User Config Templates

**Current Status:**
- Contains personal paths and specific configurations
- Not generic templates

**Required Changes:**
- Remove personal paths and specific configurations
- Create generic templates with placeholders
- Document what each section does
- Move to `templates/` directory
- Rename to `.template` extension

### 3. Configuration Migration

Replace hardcoded values with pub-bin's config system:

**Before:**
```bash
data_dir="${HOME}/data"
bin_git_url="git@github.com:USERNAME/bin.git"  # Hardcoded username - REMOVE
```

**After:**
```bash
. ${script_dir}/../config/config.sh
load-config "noerror"

# Setup interactively if missing
if [ -z "${data_dir:-}" ] ; then
    data_dir=$(setup-config-value "data_dir" \
        "Base data directory for repositories" \
        "${HOME}/data" \
        "false")
    save-config-value "data_dir" "${data_dir}"
fi
```

### 4. Documentation Requirements

Create comprehensive `system-setup/README.md`:

**Required Sections:**
- Overview of what the setup process does
- Prerequisites (macOS, Homebrew, etc.)
- Step-by-step guide
- Configuration options
- Troubleshooting section
- List of all software that gets installed
- Customization guide
- Examples of usage

### 5. Testing Considerations

**Challenges:**
- Most scripts require interactive input (not easily testable)
- System-level changes (installing software, modifying configs)

**Recommendations:**
- Consider adding `-n` (dry-run) flags where possible
- Test individual install scripts in isolation
- Document manual testing procedures
- Add validation checks before destructive operations

### 6. Security & Privacy

**CRITICAL:** The following files contain hardcoded personal information, usernames, and specific path structures that must be removed or templated before migration to pub-bin.

**NOTE:** Detailed sensitive information including specific usernames, company names, and file paths has been redacted from this document for security reasons. See [system-setup-migration-plan-sensitive.md](system-setup-migration-plan-sensitive.md) for the complete detailed analysis. **This sensitive file is excluded from git via `.gitignore` and will not be available in the remote repository.**

#### 6.1 Personal Username References

**Status:** Detailed information redacted. See [system-setup-migration-plan-sensitive.md](system-setup-migration-plan-sensitive.md) section 6.1.

**Summary:**
- Multiple instances of hardcoded usernames in `setup-system.sh` and `user-configs/bash_profile`
- Usernames appear in GitHub URLs, directory paths, and environment variable paths
- All instances must be replaced with config variables, placeholders, or `${USER}`/`${HOME}` variables

#### 6.2 Company/Organization-Specific Paths

**Status:** Detailed information redacted. See [system-setup-migration-plan-sensitive.md](system-setup-migration-plan-sensitive.md) section 6.2.

**Summary:**
- Company-specific paths found in user configuration files
- These should be removed or marked as optional with clear documentation

#### 6.3 Hardcoded Path Structures

**File: `setup-system.sh`**
- **Line 75:** `. ${data_dir}/bin/load-ssh-key.sh`
  - **Issue:** Assumes specific directory structure `${data_dir}/bin/`
  - **Risk:** May not work for all users, exposes expected structure
  - **Fix:** Make path configurable or detect automatically

- **Line 103:** `cat ${HOME}/.ssh/id_rsa.pub`
  - **Issue:** Displays SSH public key (not sensitive but personal)
  - **Risk:** Low risk, but exposes public key fingerprint
  - **Fix:** Add option to skip or suppress output, or use `-q` flag

- **Line 135:** `data_dir="${HOME}/data"`
  - **Issue:** Hardcoded default data directory
  - **Risk:** Assumes user wants `~/data` structure
  - **Fix:** Use config system with interactive setup

- **Line 136:** `keepass="/Applications/KeePassX.app/Contents/MacOS/KeePassX"`
  - **Issue:** Hardcoded macOS application path
  - **Risk:** macOS-specific, won't work on Linux
  - **Fix:** Detect OS and application location automatically

- **Line 137:** `chrome="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"`
  - **Issue:** Hardcoded macOS application path
  - **Risk:** macOS-specific, won't work on Linux
  - **Fix:** Detect OS and application location automatically

- **Line 138:** `keepass_db="${data_dir}/keepass_tmp.kdbx"`
  - **Issue:** Hardcoded database filename
  - **Risk:** Assumes specific naming convention
  - **Fix:** Make configurable or use more generic name

#### 6.4 References to Non-Existent Systems

**File: `setup-bin-config.sh`**
- **Line 11:** `. ${bin_dir}/bin-config.sh`
  - **Issue:** References old `bin-config.sh` system that doesn't exist in pub-bin
  - **Risk:** Script will fail, exposes dependency on old system
  - **Fix:** Remove script entirely or replace with pub-bin's `config/config.sh` system

#### 6.5 User Configuration Files

**Status:** Detailed information redacted. See [system-setup-migration-plan-sensitive.md](system-setup-migration-plan-sensitive.md) section 6.5.

**Summary:**
- `user-configs/bash_profile` contains extensive personal configuration
- Includes personal directory structures, company-specific paths, and hardcoded usernames
- **Risk:** High - entire file is personal configuration, not a template
- **Fix:**
  - Convert to template with placeholders
  - Remove all personal references
  - Document each section's purpose
  - Use environment variables or config system for paths
  - Mark company-specific sections as optional

**File: `user-configs/emacs`**
- **Status:** ✅ Appears clean - no personal information detected
- **Note:** Review to ensure no personal keybindings or paths

#### 6.6 Summary of Required Actions

**Status:** Detailed sensitive information redacted. See [system-setup-migration-plan-sensitive.md](system-setup-migration-plan-sensitive.md) section 6.6 for specific usernames and company names.

1. **Remove all hardcoded usernames:**
   - Replace all personal usernames with `${USER}` or config variables
   - Replace hardcoded GitHub usernames with config variables or interactive prompts
   - Replace hardcoded full paths with `${HOME}` or config variables

2. **Remove company-specific paths:**
   - Remove or mark as optional all company-specific paths
   - Document that company-specific paths should be added by users

3. **Convert user configs to templates:**
   - Replace all personal paths with placeholders
   - Add comments explaining each section
   - Use environment variables where appropriate
   - Mark optional sections clearly

4. **Use pub-bin's config system:**
   - Replace hardcoded values with `config/config.sh` functions
   - Use `setup-config-value` for interactive configuration
   - Store user-specific values in `~/.config/pub-bin/config`

5. **Make paths configurable:**
   - All hardcoded paths should be configurable
   - Provide sensible defaults
   - Allow users to customize during setup

6. **Review for sensitive data:**
   - No API keys, tokens, or credentials found ✅
   - SSH key handling is appropriate (uses standard locations)
   - No passwords or secrets in scripts ✅

### 7. Migration Priority

#### High Priority (Core Functionality)
1. **`setup-system.sh`** - Main script, needs most work
2. **`create-key.sh`** - Standalone utility, relatively clean
3. **`software-installs.sh`** - Good pattern, minor updates needed

#### Medium Priority (Supporting Scripts)
4. **Individual software install scripts** - Standardize patterns
5. **`setup-remote-syslogd.sh`** - macOS-specific, document well (see [detailed analysis](system-setup-remote-syslogd-analysis.md))

#### Low Priority (Templates/Configs)
6. **User config templates** - Clean up and template-ize
7. **`setup-bin-config.sh`** - Remove or replace entirely

### 8. Specific Recommendations

1. **Make it optional:** Allow users to skip steps (e.g., KeePassX, GitHub setup)
2. **Add validation:** Check prerequisites before starting
3. **Improve error messages:** More descriptive failures
4. **Add logging:** Option to log all setup steps to a file
5. **Support different environments:** Detect macOS vs Linux, handle both
6. **Modular execution:** Allow running individual setup steps independently

### 9. Questions to Consider

1. **Should `create-ssh-key.sh` be in root or system-setup?**
   - **Recommendation:** Root if standalone utility, system-setup if only used during setup

2. **Should user configs be templates or examples?**
   - **Recommendation:** Templates with placeholders

3. **How to handle macOS-specific vs cross-platform?**
   - **Recommendation:** Detect OS, skip macOS-only steps on Linux

4. **Should this be a one-time setup or repeatable?**
   - **Recommendation:** Make it idempotent (can run multiple times safely)

## Next Steps

1. Review and revise this plan
2. Create migration task list
3. Begin with high-priority scripts
4. Test each migrated script
5. Update documentation as we go
