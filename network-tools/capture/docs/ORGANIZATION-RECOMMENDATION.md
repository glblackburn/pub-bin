# Organization Recommendation for network-tools/capture/

## Current Structure Analysis

### Files in Root Directory (14 files)

**Main Scripts (3):**
- `analyze-tcpdump.py` - Main analysis tool (831 lines)
- `record-tcpdump.sh` - Script to record tcpdump captures
- `sanitize-analysis-ipmask.py` - IP masking sanitization (current, 356 lines)

**Documentation (6):**
- `docs/bugs/bug-1.md` - Bug documentation (pytest installation)
- `docs/bugs/bug-2.md` - Bug documentation (linting tools)
- `docs/bugs/bug-3.md` - Bug documentation (mypy installation)
- `docs/sanitization/ipmask-example-mapping.md` - Example IP mappings (213 lines)
- `docs/sanitization/sanitize-analysis-output.md` - Sanitization strategy documentation (155 lines)
- `docs/test-coverage-analysis.md` - Test coverage analysis and recommendations

**Configuration (3):**
- `Makefile` - Build, test, lint, type-check targets
- `.flake8` - Flake8 linting configuration
- `.gitignore` - Git ignore rules

**Directories:**
- `tests/` - Test suite (3 test files + test data)
- `log/` - Output files (tcpdump captures and analysis results)

## Recommended Organization

### Option 1: Minimal Reorganization (Recommended)

Keep main scripts in root, organize documentation into subdirectories:

```
network-tools/capture/
├── analyze-tcpdump.py          # Main tool (keep in root)
├── record-tcpdump.sh           # Recording script (keep in root)
├── sanitize-analysis-ipmask.py # Current sanitization (keep in root)
├── Makefile                    # Build config (keep in root)
├── .flake8                     # Lint config (keep in root)
├── .gitignore                  # Git config (keep in root)
│
├── docs/                       # NEW: Documentation directory
│   ├── bugs/                   # Bug documentation
│   │   ├── bug-1.md
│   │   ├── bug-2.md
│   │   └── bug-3.md
│   ├── sanitization/            # Sanitization documentation
│   │   ├── sanitize-analysis-output.md
│   │   └── ipmask-example-mapping.md
│   └── test-coverage-analysis.md
│
├── tests/                      # Test suite (keep as-is)
│   ├── conftest.py
│   ├── test_analyze_tcpdump.py
│   ├── test_cli_integration.py
│   ├── test_sanitize_ipmask.py
│   └── data/
│       └── tcpdump/
│
├── log/                        # Output files (keep as-is)
│   └── [tcpdump and analysis files]
│
└── README.md                   # NEW: Main documentation
```

**Rationale:**
- Main scripts stay accessible in root (common pattern)
- Documentation grouped logically
- Minimal disruption to existing workflows
- Clear separation of concerns

### Option 2: Scripts Directory

Group all scripts together:

```
network-tools/capture/
├── scripts/                    # NEW: All scripts
│   ├── analyze-tcpdump.py
│   ├── record-tcpdump.sh
│   └── sanitize-analysis-ipmask.py
│
├── docs/                       # Documentation (same as Option 1)
│   ├── bugs/
│   ├── sanitization/
│   └── test-coverage-analysis.md
│
├── tests/                      # Test suite
├── log/                        # Output files
├── Makefile                    # Updated paths
├── .flake8
├── .gitignore
└── README.md
```

**Rationale:**
- All scripts in one place
- Cleaner root directory
- Requires updating Makefile and import paths

### Option 3: Tool-Based Organization

Organize by tool/feature:

```
network-tools/capture/
├── analyze-tcpdump/            # Main tool directory
│   ├── analyze-tcpdump.py
│   ├── tests/
│   │   ├── test_analyze_tcpdump.py
│   │   ├── test_cli_integration.py
│   │   └── data/
│   └── docs/
│       └── test-coverage-analysis.md
│
├── sanitize/                   # Sanitization tool directory
│   ├── sanitize-analysis-ipmask.py
│   ├── tests/
│   │   └── test_sanitize_ipmask.py
│   └── docs/
│       ├── sanitize-analysis-output.md
│       └── ipmask-example-mapping.md
│
├── record-tcpdump.sh           # Recording script (root)
├── docs/                       # Shared documentation
│   └── bugs/
│       ├── bug-1.md
│       ├── bug-2.md
│       └── bug-3.md
│
├── log/                        # Output files
├── Makefile                    # Updated paths
├── .flake8
├── .gitignore
└── README.md
```

**Rationale:**
- Self-contained tool directories
- Each tool has its own tests and docs
- More modular structure
- Requires significant restructuring

## Recommendation: Option 1 (Minimal Reorganization)

### Why Option 1?

1. **Minimal Disruption**: Main scripts stay in root (common pattern for CLI tools)
2. **Clear Organization**: Documentation grouped logically without over-engineering
3. **Easy Navigation**: Developers can find scripts quickly, docs are organized
4. **Maintainable**: Simple structure that scales well

### Implementation Steps

1. **Create directories:**
   ```bash
   mkdir -p docs/bugs docs/sanitization
   ```

2. **Move files:** ✅ **COMPLETED**
   ```bash
   mv bug-*.md docs/bugs/
   mv sanitize-analysis-output.md docs/sanitization/
   mv ipmask-example-mapping.md docs/sanitization/
   mv test-coverage-analysis.md docs/
   mv ORGANIZATION-RECOMMENDATION.md docs/
   ```

3. **Remove deprecated file:** ✅ **COMPLETED**
   - Removed `sanitize-analysis.py` (deprecated, replaced by `sanitize-analysis-ipmask.py`)

4. **Create README.md** (if missing) with:
   - Overview of tools
   - Quick start guide
   - Links to documentation
   - Usage examples

5. **Update references:**
   - Update any links in documentation
   - Update Makefile if it references doc paths
   - Update .gitignore if needed

### Additional Recommendations

1. **Create README.md** in root:
   - Tool overview
   - Quick start
   - Links to detailed docs
   - Examples

2. **Consider consolidating sanitization docs:**
   - Merge `sanitize-analysis-output.md` and `ipmask-example-mapping.md` into single doc
   - Or keep separate: one for strategy, one for examples

3. **Bug documentation:**
   - Consider moving resolved bugs to `docs/bugs/resolved/`
   - Keep active bugs in `docs/bugs/`

4. **Add .gitignore entries** for:
   - `__pycache__/`
   - `*.pyc`
   - `.pytest_cache/`
   - `.mypy_cache/`
   - `htmlcov/`
   - `coverage.xml`
   - `log/*.txt` (or specific patterns)

5. **Consider adding:**
   - `CHANGELOG.md` - Version history
   - `CONTRIBUTING.md` - Development guidelines
   - `LICENSE` - If applicable

## File Count Summary

**Current:**
- Root: 14 files (scripts, docs, config)
- Tests: 3 test files + 10 test data files
- Log: 8 output files

**After Option 1:**
- Root: 7 files (scripts + config)
- docs/: 6 documentation files
- Tests: Same (3 test files + 10 test data files)
- Log: Same (8 output files)

## Next Steps

1. Review this recommendation
2. Choose organization option
3. Implement file moves
4. Update documentation links
5. Create/update README.md
6. Test that everything still works
7. Commit changes
