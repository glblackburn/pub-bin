# Record Scripts Analysis

Analysis of all `record*` scripts in the `../bin` folder.

**Status**: ✅ Migrated to `pub-bin` with "By Tool Type" organization structure.

## Summary

Found **9 record scripts** (excluding backup files with `~` suffix) that capture and timestamp various system and network information. These scripts follow a common pattern: execute a command, capture output with timestamps, and save to timestamped files.

**Migration Status**: All 9 record scripts have been migrated to `pub-bin` and organized by tool type:
- `network-tools/diagnostics/` - 3 scripts
- `network-tools/scanning/` - 1 script
- `network-tools/intelligence/` - 2 scripts
- `network-tools/capture/` - 1 script
- `system-tools/` - 2 scripts

## Categorization

### 1. Network Diagnostics & Lookup Tools (6 scripts)

These scripts record network-related information for troubleshooting and analysis.

#### **record-netstat.sh**
- **Purpose**: Records network connection information
- **Command**: `netstat -an`
- **Output**: `record-netstat_YYYY-MM-DD_HHMMSS.txt`
- **Use Case**: Monitor active network connections, ports, and listening services
- **Category**: Network Monitoring

#### **record-nmap.sh**
- **Purpose**: Records network port scanning results
- **Command**: `nmap -Pn -oG <target>`
- **Output**: `<target>_nmap_oG_YYYY-MM-DD_HHMMSS.txt`
- **Parameters**: Requires target IP/hostname as argument
- **Use Case**: Security scanning, port discovery, service enumeration
- **Category**: Network Security Scanning

#### **record-nslookup.sh**
- **Purpose**: Records DNS lookup results for IP addresses
- **Command**: `nslookup <ip>`
- **Output**: `nslookup_<ip>_YYYY-MM-DD_HHMMSS.txt`
- **Parameters**: Requires IP address as argument
- **Use Case**: DNS troubleshooting, reverse DNS lookups, IP-to-hostname resolution
- **Category**: DNS Diagnostics

#### **record-whois.sh**
- **Purpose**: Records WHOIS information for IP addresses
- **Command**: `whois <ip>`
- **Output**: `whois_<ip>_YYYY-MM-DD_HHMMSS.txt`
- **Parameters**: Requires IP address as argument
- **Use Case**: IP ownership lookup, network block information, abuse contact details
- **Category**: IP Intelligence

#### **record-ip-api-json.sh**
- **Purpose**: Records IP API/WHOIS data in JSON format
- **Command**: `ip-api-json.sh <ip>` (calls another script)
- **Output**: `ip-api-whois_<ip>_YYYY-MM-DD_HHMMSS.txt`
- **Parameters**: Requires IP address as argument
- **Use Case**: Structured IP information retrieval, API-based lookups
- **Category**: IP Intelligence / API Integration

#### **netmon/record-network-config.sh**
- **Purpose**: Records network interface configuration
- **Commands**: 
  - `ifconfig` (all interfaces)
  - `ifconfig en0` (WiFi interface)
  - `ifconfig en7` (LAN interface)
- **Output**: 
  - `net_all_info.txt`
  - `net_wifi_info.txt`
  - `net_lan_info.txt`
- **Use Case**: Network configuration snapshots, interface status, IP address changes
- **Category**: Network Configuration Monitoring

#### **netmon/record-tcpdump.sh**
- **Purpose**: Records network packet captures
- **Command**: `sudo tcpdump -n`
- **Output**: `log/record-tcpdump_YYYY-MM-DD_HHMMSS.txt`
- **Note**: Requires sudo privileges, runs continuously until stopped
- **Use Case**: Deep packet inspection, network traffic analysis, security monitoring
- **Category**: Network Packet Capture

### 2. System Monitoring (2 scripts)

These scripts record system-level information and events.

#### **record-uptime.sh**
- **Purpose**: Records system uptime information
- **Command**: `uptime`
- **Output**: `record-uptime_YYYY-MM-DD_HHMMSS.txt`
- **Use Case**: System availability tracking, load average monitoring, uptime history
- **Category**: System Health Monitoring

#### **record-log-show.sh**
- **Purpose**: Records macOS login/logout events from system logs
- **Command**: `log show --start <today> --style syslog --predicate 'process == "loginwindow"'`
- **Output**: `~/log/log-show_YYYY-MM-DD_HHMMSS.log`
- **Special Processing**: Filters for "LWScreenLock startUnlock" and "inform UA unlocked" events
- **Use Case**: Security auditing, login tracking, screen unlock monitoring
- **Category**: Security Auditing / System Events

## Common Patterns

### Shared Characteristics:
1. **Timestamping**: All scripts use `date +%Y-%m-%d_%H%M%S` format for timestamps
2. **Output Files**: Most create timestamped output files in current directory
3. **Command Execution**: Execute a system/network command and capture output
4. **Tee Usage**: Many use `tee` to both display and save output
5. **Error Handling**: Most use `set -euET -o pipefail` for robust error handling

### Variations:
- **Parameter Requirements**: Some require arguments (IP addresses, targets), others don't
- **Output Location**: Most use current directory, `record-log-show.sh` uses `~/log/`, `record-tcpdump.sh` uses `log/` subdirectory
- **Continuous vs. Snapshot**: Most are one-time snapshots, `record-tcpdump.sh` runs continuously
- **Privileges**: `record-tcpdump.sh` requires sudo

## Suggested Organization

**Recommended: Option 2 (By Tool Type)** - See detailed expansion below.

### Option 1: By Function
```
network-monitoring/
  ├── record-netstat.sh
  ├── record-nmap.sh
  ├── record-nslookup.sh
  ├── record-whois.sh
  ├── record-ip-api-json.sh
  └── netmon/
      ├── record-network-config.sh
      └── record-tcpdump.sh

system-monitoring/
  ├── record-uptime.sh
  └── record-log-show.sh
```

### Option 2: By Tool Type (Recommended)

```
pub-bin/
├── network-tools/
│   ├── diagnostics/
│   │   ├── record-netstat.sh
│   │   ├── record-nslookup.sh
│   │   └── record-network-config.sh
│   ├── scanning/
│   │   └── record-nmap.sh
│   ├── intelligence/
│   │   ├── record-whois.sh
│   │   └── record-ip-api-json.sh
│   └── capture/
│       └── record-tcpdump.sh
└── system-tools/
    ├── record-uptime.sh
    └── record-log-show.sh
```

#### Rationale

**Advantages of Tool Type Organization:**

1. **Clear Functional Grouping**
   - Scripts grouped by what they do, not just where they run
   - Easy to find tools for specific tasks: "I need network diagnostics" → `network-tools/diagnostics/`
   - Logical hierarchy: category → subcategory → script
   - Makes the purpose and relationship between scripts immediately clear

2. **Scalability**
   - Easy to add new categories (e.g., `security-tools/`, `performance-tools/`)
   - Easy to add new subcategories within existing categories
   - Structure grows organically as new tools are added
   - No need to decide "root vs subdirectory" for each new script

3. **Better Discoverability**
   - Users can browse by category to find related tools
   - Related tools are co-located (all diagnostics together, all scanning together)
   - Reduces cognitive load: "I need to scan something" → `network-tools/scanning/`
   - Clear mental model: tools organized by function

4. **Maintenance Benefits**
   - Easier to maintain related scripts together
   - Can create category-specific READMEs
   - Can share common code within categories
   - Easier to identify gaps: "We have diagnostics and scanning, but no monitoring?"

5. **Professional Organization**
   - Matches common software project structures
   - Looks more organized and intentional
   - Easier for new users to understand the codebase
   - Better for documentation and onboarding

#### Structure Details

**network-tools/diagnostics/** (3 scripts)
- **Purpose**: Network connection and configuration diagnostics
- **Scripts**:
  - `record-netstat.sh` - Active connections and ports
  - `record-nslookup.sh` - DNS resolution
  - `record-network-config.sh` - Interface configuration
- **Use Case**: Troubleshooting network issues, checking connectivity
- **Common Pattern**: One-time snapshots of network state

**network-tools/scanning/** (1 script)
- **Purpose**: Network security scanning and enumeration
- **Scripts**:
  - `record-nmap.sh` - Port scanning and service detection
- **Use Case**: Security audits, service discovery, vulnerability assessment
- **Common Pattern**: Active probing of network targets

**network-tools/intelligence/** (2 scripts)
- **Purpose**: IP address and network block information gathering
- **Scripts**:
  - `record-whois.sh` - WHOIS lookups
  - `record-ip-api-json.sh` - API-based IP information
- **Use Case**: Threat intelligence, IP attribution, network research
- **Common Pattern**: External lookups for IP metadata

**network-tools/capture/** (1 script)
- **Purpose**: Deep packet inspection and traffic capture
- **Scripts**:
  - `record-tcpdump.sh` - Packet capture
- **Use Case**: Network forensics, traffic analysis, security monitoring
- **Common Pattern**: Continuous capture (runs until stopped, requires sudo)

**system-tools/** (2 scripts)
- **Purpose**: System-level monitoring and event logging
- **Scripts**:
  - `record-uptime.sh` - System uptime and load
  - `record-log-show.sh` - macOS system events
- **Use Case**: System health monitoring, security auditing, availability tracking
- **Common Pattern**: System state snapshots and event logs

#### Migration Plan

**Phase 1: Create Directory Structure**
```bash
mkdir -p network-tools/{diagnostics,scanning,intelligence,capture}
mkdir -p system-tools
```

**Phase 2: Move Scripts**
```bash
# Network diagnostics
mv record-netstat.sh network-tools/diagnostics/
mv record-nslookup.sh network-tools/diagnostics/
mv netmon/record-network-config.sh network-tools/diagnostics/

# Network scanning
mv record-nmap.sh network-tools/scanning/

# Network intelligence
mv record-whois.sh network-tools/intelligence/
mv record-ip-api-json.sh network-tools/intelligence/

# Network capture
mv netmon/record-tcpdump.sh network-tools/capture/

# System tools
mv record-uptime.sh system-tools/
mv record-log-show.sh system-tools/
```

**Phase 3: Create README Files**

**network-tools/README.md:**
```markdown
# Network Tools

Network diagnostic, scanning, intelligence, and capture tools.

## Categories

- **diagnostics/** - Network connection and configuration diagnostics
- **scanning/** - Network security scanning and enumeration
- **intelligence/** - IP address and network block information
- **capture/** - Deep packet inspection and traffic capture

## Quick Reference

### Diagnostics
- `diagnostics/record-netstat.sh` - Network connections
- `diagnostics/record-nslookup.sh <ip>` - DNS lookups
- `diagnostics/record-network-config.sh` - Interface configuration

### Scanning
- `scanning/record-nmap.sh <target>` - Port scanning

### Intelligence
- `intelligence/record-whois.sh <ip>` - WHOIS lookups
- `intelligence/record-ip-api-json.sh <ip>` - IP API data

### Capture
- `capture/record-tcpdump.sh` - Packet capture (requires sudo)
```

**system-tools/README.md:**
```markdown
# System Tools

System-level monitoring and event logging tools.

- `record-uptime.sh` - System uptime and load
- `record-log-show.sh` - macOS login/logout events
```

**Phase 4: Update Scripts**
- Update any hardcoded paths in scripts
- Update any references to other scripts
- Ensure output directory handling works from new locations
- Test all scripts from new locations

**Phase 5: Create Symlinks (Optional, for backward compatibility)**
```bash
# Create symlinks at root for commonly used scripts
ln -s network-tools/diagnostics/record-netstat.sh record-netstat.sh
ln -s network-tools/scanning/record-nmap.sh record-nmap.sh
ln -s system-tools/record-uptime.sh record-uptime.sh
```

#### Enhancements for Tool Type Structure

**1. Category-Specific Configuration**
```bash
# network-tools/.config
NETWORK_OUTPUT_DIR="${HOME}/logs/network"

# system-tools/.config
SYSTEM_OUTPUT_DIR="${HOME}/logs/system"
```

**2. Category-Specific Libraries**
```bash
# network-tools/lib/network-common.sh
# Shared functions for network tools

# system-tools/lib/system-common.sh
# Shared functions for system tools
```

**3. Category Wrapper Scripts**
```bash
# network-tools/run-diagnostics.sh
# Run all diagnostic tools in sequence

# network-tools/run-intelligence.sh <ip>
# Run all intelligence tools for an IP
```

**4. Category Documentation**
- Each category can have its own README with specific use cases
- Category-specific examples and workflows
- Category-specific troubleshooting guides

**5. Consistent Naming Within Categories**
- All scripts in `diagnostics/` follow same pattern
- All scripts in `intelligence/` follow same pattern
- Makes it easier to understand what each script does

#### Benefits Over Current Structure

1. **Better Organization**: Related tools are grouped together
2. **Easier Navigation**: Clear path to find specific tool types
3. **Scalability**: Easy to add new categories or subcategories
4. **Professional**: Matches common software project organization
5. **Maintainability**: Related code is co-located
6. **Documentation**: Can have category-specific docs
7. **Discovery**: Users can browse by function to find tools

#### Potential Concerns & Solutions

**Concern**: Longer paths to execute scripts
- **Solution**: Create symlinks for commonly used scripts
- **Solution**: Add scripts to PATH or create aliases
- **Solution**: Create wrapper scripts at root level

**Concern**: Breaking existing workflows
- **Solution**: Create symlinks for backward compatibility
- **Solution**: Document migration clearly
- **Solution**: Phase migration (move scripts, test, then remove old locations)

**Concern**: More directories to navigate
- **Solution**: Clear README files in each directory
- **Solution**: Create index/quick reference at root
- **Solution**: Use tab completion and aliases

#### Future Expansion Possibilities

With this structure, easy to add:
- `security-tools/` - Security-specific recording tools
- `performance-tools/` - Performance monitoring tools
- `network-tools/monitoring/` - Continuous monitoring (if different from capture)
- `system-tools/processes/` - Process-specific monitoring
- `network-tools/analysis/` - Post-capture analysis tools

### Option 3: Keep Current Structure

```
pub-bin/
├── record-netstat.sh          # Root level - commonly used
├── record-nmap.sh
├── record-nslookup.sh
├── record-whois.sh
├── record-ip-api-json.sh
├── record-uptime.sh
├── record-log-show.sh
└── netmon/
    ├── record-network-config.sh
    └── record-tcpdump.sh
```

#### Rationale

**Advantages of Current Structure:**

1. **Accessibility & Discoverability**
   - Common tools at root level are easy to find and execute
   - No need to navigate subdirectories for frequently used scripts
   - Simple `./record-netstat.sh` vs `./network-tools/diagnostics/record-netstat.sh`
   - Matches user mental model: "I need to record something" → look for `record-*` at root

2. **Logical Grouping**
   - Root level scripts are **general-purpose** tools used across different scenarios
   - `netmon/` subdirectory contains **specialized** network monitoring tools
   - Clear distinction: general diagnostics vs. continuous monitoring
   - `netmon/` scripts are related to each other (both network monitoring, both in same context)

3. **Minimal Disruption**
   - Current structure already works
   - No need to update documentation, scripts, or workflows
   - Users already familiar with current locations
   - Less risk of breaking existing automation/aliases

4. **Scalability**
   - Easy to add new general record scripts at root level
   - Easy to add specialized tools to `netmon/` if needed
   - Can create other specialized subdirectories if needed (e.g., `security/record-*.sh`)

5. **Naming Convention Clarity**
   - All scripts follow `record-<tool>.sh` pattern
   - Easy to find all record scripts: `ls record*.sh`
   - Consistent naming makes it clear they're related tools

#### Current Structure Analysis

**Root Level Scripts (7 scripts):**
- **Purpose**: Quick, one-off recordings of system/network state
- **Usage Pattern**: Run when needed, get timestamped output file
- **Dependencies**: Minimal (mostly standard system commands)
- **User Type**: General users, troubleshooting, ad-hoc diagnostics

**netmon/ Subdirectory (2 scripts):**
- **Purpose**: Continuous or specialized network monitoring
- **Usage Pattern**: 
  - `record-network-config.sh`: Snapshot of network config (multiple interfaces)
  - `record-tcpdump.sh`: Continuous packet capture (runs until stopped)
- **Dependencies**: 
  - `record-tcpdump.sh` requires sudo
  - Both are more specialized/advanced use cases
- **User Type**: Network administrators, security analysts, advanced users

#### Enhancements While Keeping Structure

**1. Add README.md to netmon/ subdirectory:**
```markdown
# Network Monitoring Tools

Specialized network monitoring and capture tools.

- `record-network-config.sh` - Capture network interface configurations
- `record-tcpdump.sh` - Continuous packet capture (requires sudo)

See parent directory for general network diagnostic tools.
```

**2. Create shared library for common functions:**
```bash
# lib/record-common.sh
get_timestamp() { date +%Y-%m-%d_%H%M%S; }
get_output_dir() { echo "${RECORD_OUTPUT_DIR:-.}"; }
ensure_output_dir() { mkdir -p "$(get_output_dir)"; }
```

**3. Standardize output directory (optional config):**
- Add `~/.config/pub-bin/record-output-dir` config
- Default to current directory (backward compatible)
- Allow override via environment variable: `RECORD_OUTPUT_DIR=~/logs/record`

**4. Add consistent CLI options:**
```bash
# All scripts could support:
--output-dir DIR    # Override output directory
--quiet            # Suppress console output
--help             # Show usage
```

**5. Create index/README at root:**
```markdown
# Record Scripts

Quick reference for all record scripts:

## Network Diagnostics
- `record-netstat.sh` - Network connections
- `record-nmap.sh <target>` - Port scanning
- `record-nslookup.sh <ip>` - DNS lookups
- `record-whois.sh <ip>` - IP ownership
- `record-ip-api-json.sh <ip>` - IP API data

## System Monitoring
- `record-uptime.sh` - System uptime
- `record-log-show.sh` - macOS login events

## Specialized Network Monitoring
See `netmon/` subdirectory for advanced network monitoring tools.
```

#### When to Reconsider Structure

**Consider reorganization if:**
- Number of record scripts grows significantly (20+)
- Need for multiple specialized subdirectories emerges
- Users report difficulty finding scripts
- Need for script versioning or multiple variants

**Signs current structure is working:**
- ✅ Scripts are easy to find (`ls record*.sh`)
- ✅ Clear separation between general and specialized
- ✅ No user complaints about organization
- ✅ Simple mental model (root = general, subdir = specialized)

#### Migration Strategy (If Keeping Structure)

1. **Phase 1: Standardization** (No structure changes)
   - Add shared library for common functions
   - Standardize CLI options across all scripts
   - Add consistent error handling
   - Document output directory behavior

2. **Phase 2: Enhancement** (No structure changes)
   - Add `--help` to all scripts
   - Add `--output-dir` option
   - Create README files
   - Add usage examples

3. **Phase 3: Optional Improvements** (Still no structure changes)
   - Consider log rotation/cleanup utilities
   - Add script to list all record outputs
   - Create wrapper script for common operations

**Key Principle**: Enhance functionality and usability without changing file locations.

## Recommendations

1. **Standardization Opportunities**:
   - All scripts could use a common output directory (e.g., `~/logs/record/`)
   - Standardize timestamp format across all scripts
   - Add `--help` flags to all scripts
   - Consider a shared library for common functions (timestamp generation, output directory management)

2. **Documentation**:
   - Add usage examples to each script
   - Document required parameters
   - Note privilege requirements (sudo for tcpdump)

3. **Enhancements**:
   - Add `--output-dir` option to specify where files are saved
   - Add `--quiet` flag to suppress console output
   - Add `--append` option for continuous logging
   - Consider adding cleanup of old log files (retention policy)

4. **Migration Priority** (if reorganizing to By Tool Type):
   - **Phase 1**: Create directory structure and move scripts
   - **Phase 2**: Create README files for each category
   - **Phase 3**: Update scripts for new paths
   - **Phase 4**: Create symlinks for backward compatibility (optional)
   - **Phase 5**: Test and document new structure

## File Count Summary

- **Total record scripts**: 9
- **Network Diagnostics**: 6
- **System Monitoring**: 2
- **Backup files (with ~)**: 3 (can be removed)
