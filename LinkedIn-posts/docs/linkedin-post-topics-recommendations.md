# LinkedIn Post Topics - Recommended Subjects

**Generated:** December 7, 2025
**Last Updated:** December 9, 2025
**Purpose:** Recommendations for LinkedIn posts about scripts that haven't been covered or have had significant updates

## High Priority - Recent Significant Updates

### ✅ React2Shell Server: Building a Security Testing Testbed
- **Status:** ✅ Published December 9, 2025 (Part 1 of 4-part series)
- **Story:** Comprehensive security testing testbed for validating scanner detection
- **Key Points:**
  - React/Next.js version switching for vulnerability testing
  - Dual framework support (Vite and Next.js)
  - Framework-aware Express server
  - Comprehensive Selenium test suite (28 tests)
  - Performance tracking and optimization (52% improvement)
  - Scanner verification automation
- **Visual Appeal:** Framework architecture, test output, performance metrics
- **Technical Interest:** Security testing, framework-aware architecture, test automation, performance optimization
- **Note:** Parts 2-4 are drafted and ready to post

### ✅ `monitor-ai-agent-progress.sh`: Recent Feature Improvements (FEATURE-1 & FEATURE-2)
- **Status:** ⏳ Not yet posted - High priority
- **Story:** Two major improvements completed December 9, 2025 - accurate git status counting and process count monitoring
- **Key Points:**
  - **FEATURE-1:** Improved git status counting - accurately counts all untracked files including those in directories using `find`
  - **FEATURE-2:** Added process count monitoring with `-p` flag (off by default)
  - Fixed alignment issues for all metrics
  - Handles both staged and unstaged modifications correctly
  - Cross-platform process counting using `ps -e`
  - Framework-aware improvements following defect tracking pattern
- **Visual Appeal:** Before/after comparison of git status accuracy, process monitoring output
- **Technical Interest:** Git internals, process monitoring, cross-platform compatibility, incremental feature development
- **Commits:** 1012459 (FEATURE-1), 3e8ac64 (FEATURE-2)

### ✅ `what-is-left.py`: From bash to Python with multi-column layout
- **Status:** ✅ Published December 7, 2025
- **Story:** Migration from bash to Python with enhanced features
- **Key Points:**
  - Multi-column layout for wide terminals
  - Git history analysis for migration tracking
  - Rich library for color-coded output
  - Terminal width detection and adaptive formatting
- **Visual Appeal:** Great before/after comparison, color-coded output screenshots
- **Technical Interest:** Python vs bash decision, rich library usage, terminal UI design

### • Record scripts refactoring: Standardizing 9 network and system tools
- **Story:** Refactored all `record*.sh` scripts to follow `shell-template.sh` patterns
- **Key Points:**
  - Organized by tool type (diagnostics, scanning, intelligence, capture)
  - Added consistent CLI options, error handling, and usage functions
  - Migration from scattered scripts to organized structure
- **Visual Appeal:** Before/after code comparison, organized directory structure
- **Technical Interest:** Code standardization, refactoring patterns, organization strategy

### • BATS testing framework: Comprehensive test suites for shell scripts
- **Story:** Built comprehensive test suites for `load-ssh-key.sh` and all `record*.sh` scripts
- **Key Points:**
  - Test structure with helpers, assertions, and test runners
  - 40+ tests covering script existence, command availability, argument validation, output file creation
  - Testing patterns for network commands and system tools
- **Visual Appeal:** Test output screenshots, test structure diagrams
- **Technical Interest:** Testing shell scripts, BATS framework, test coverage strategies

## Medium Priority - Interesting Projects/Tools

### • Arecibo Message decoding: First-principles binary analysis
- **Story:** Complete Python toolkit for decoding the Arecibo Message
- **Key Points:**
  - Step-by-step analysis scripts (6 Python scripts)
  - Educational value and verifiable analysis
  - AI-generated code that proves its work
- **Visual Appeal:** Decoded message visualizations, step-by-step analysis output
- **Technical Interest:** Binary analysis, first-principles thinking, educational projects

### • GreyNoise API integration: Threat intelligence lookups
- **Story:** `greynoise-lookup.sh` for IP threat intelligence
- **Key Points:**
  - Community API integration (no key required)
  - IP validation and error handling
  - Security use cases
- **Visual Appeal:** API response examples, threat intelligence output
- **Technical Interest:** API integration, security tools, threat intelligence

### • Azure Entra ID sign-in log analysis
- **Story:** `azure/show-location-authenticationDetails.sh` for processing Azure logs
- **Key Points:**
  - JSON parsing with `jq`
  - Multiple output formats (table, CSV, JSON)
  - Security and compliance use cases
- **Visual Appeal:** Formatted table output, JSON structure examples
- **Technical Interest:** Azure integration, log analysis, security compliance

### • Network tools organization: Categorizing diagnostic and scanning tools
- **Story:** Organization strategy for network tools
- **Key Points:**
  - Categories: diagnostics, scanning, intelligence, capture
  - Common patterns across network scripts
  - Tool-specific documentation
- **Visual Appeal:** Directory structure, category organization
- **Technical Interest:** Code organization, tool categorization, documentation strategy

## Lower Priority - Utility Scripts

### • `shell-template.sh`: A comprehensive bash script template
- **Story:** Template demonstrating bash best practices
- **Key Points:**
  - Common patterns (CLI parsing, error handling, colors, date formatting)
  - Reference for creating new scripts
  - Standardization across the repository
- **Visual Appeal:** Template code snippets, usage examples
- **Technical Interest:** Bash best practices, code templates, standardization

### • `sort-netstat-tcp.sh`: Network connection analysis utility
- **Story:** Sorting and filtering TCP connections from netstat output
- **Key Points:**
  - Network troubleshooting workflow
  - Integration with `record-netstat.sh`
- **Visual Appeal:** Before/after netstat output comparison
- **Technical Interest:** Network troubleshooting, data processing utilities

### • System tools: macOS-specific monitoring scripts
- **Story:** `record-uptime.sh` and `record-log-show.sh` for system monitoring
- **Key Points:**
  - System uptime tracking
  - macOS login event logging
  - System monitoring patterns
- **Visual Appeal:** System log output examples
- **Technical Interest:** System monitoring, macOS-specific tools, log analysis

### • Configuration management: The `config/config.sh` library
- **Story:** Modular configuration system for all scripts
- **Key Points:**
  - Interactive setup functions
  - Secure config support
  - Reusable patterns
- **Note:** Already mentioned in Nov 11 post, but could expand with more details
- **Visual Appeal:** Interactive setup flow, config file structure
- **Technical Interest:** Configuration management, reusable libraries, secure config handling

## Meta/Process Topics

### • Migration progress: Tracking 130+ scripts from private to public repo
- **Story:** Using `what-is-left.py` to track migration
- **Key Points:**
  - Progress metrics and categorization
  - Quality improvements during migration
- **Visual Appeal:** Migration progress charts, statistics
- **Technical Interest:** Project management, migration strategies, progress tracking

### • Documentation strategy: Keeping READMEs in sync with code
- **Story:** Automated documentation updates
- **Key Points:**
  - Category-specific READMEs
  - Cross-referencing between docs
- **Note:** Expansion of Nov 12 post
- **Visual Appeal:** Documentation structure, cross-reference examples
- **Technical Interest:** Documentation practices, maintainability, knowledge management

### • AI coding standards: Establishing consistent patterns across projects
- **Story:** `README-AI-CODING-STANDARDS.md` standards
- **Key Points:**
  - Standardization across scripts
  - Code quality improvements
- **Visual Appeal:** Standards document, before/after code examples
- **Technical Interest:** Code standards, quality assurance, AI-assisted development

## Special Interest Topics

### • Testing shell scripts: BATS framework patterns and practices
- **Story:** Deep dive into BATS testing
- **Key Points:**
  - Test helpers and custom assertions
  - Testing network commands and system tools
  - Test coverage strategies
- **Visual Appeal:** Test code examples, test output
- **Technical Interest:** Testing methodologies, BATS framework, test patterns

### • Python vs Bash: When to choose which tool
- **Story:** `what-is-left.py` migration decision
- **Key Points:**
  - Rich library for terminal output
  - Git history analysis in Python
  - When bash is still the right choice
- **Visual Appeal:** Code comparison, output comparison
- **Technical Interest:** Language selection, tool choice, Python vs bash trade-offs

---

## Summary

- **Total topics:** 16+ potential posts
- **Completed:** 7 posts (including React2Shell Server Part 1)
- **High priority:** 3 topics (1 completed - React2Shell Server, 1 pending - monitor-ai-agent-progress improvements, 1 completed - what-is-left.py)
- **Medium priority:** 5 (interesting projects, useful tools)
- **Lower priority:** 4 (utility scripts, process topics)
- **Special interest:** 3 (deep dives, comparisons)
- **Draft posts ready:** React2Shell Server Parts 2-4 (pending LinkedIn URLs)

## Recommended Posting Order

1. ✅ **React2Shell Server** - ✅ Published December 9, 2025 (Part 1) - Comprehensive security testing tool, great technical story
2. **`monitor-ai-agent-progress.sh` improvements (FEATURE-1 & FEATURE-2)** - ⏳ High priority - Two major features just completed, demonstrates incremental improvement process
3. **Record scripts refactoring** - Significant work, organization story, standardization
4. **BATS testing framework** - Comprehensive testing story, quality assurance
5. **Arecibo Message project** - Unique, educational, interesting story
6. **GreyNoise/Azure tools** - Security focus, API integration

## Notes

- All topics cover scripts that haven't been featured in LinkedIn posts yet (except completed ones)
- Topics highlight recent significant updates
- Mix of technical depth and process insights
- Visual appeal varies by topic - some have great screenshots, others are more conceptual
- Consider audience interest - security tools, testing, and unique projects tend to get more engagement

## Completed Posts

- ✅ **December 9, 2025:** React2Shell Server: Building a Security Testing Testbed (Part 1 of 4)
- ✅ **December 7, 2025:** `what-is-left.py` - From bash to Python with multi-column layout
- ✅ **December 7, 2025:** AI coding assistant code review (Antigravity reviewing Cursor work)
- ✅ **December 6, 2025:** Trufflehog security scanning automation
- ✅ **December 5, 2025:** `aws-bin` - AWS SSO auto-detection
- ✅ **December 3, 2025:** `load-ssh-key.sh` - From bug fixes to comprehensive testing
- ✅ **December 2, 2025:** Is Ruby Dead?
