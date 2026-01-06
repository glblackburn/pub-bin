# Trufflehog Scripts - Feature and Defect Tree

This document provides a comprehensive tree structure of all features and defects for the trufflehog scripts.

## Structure

```
trufflehog-scripts/
├── Features
│   ├── Core Functionality
│   │   ├── Secret Rotation
│   │   │   ├── Single Secret Rotation ✅
│   │   │   ├── Paired Secret Rotation ✅
│   │   │   ├── Automatic Discovery (Phase 2) 🔄
│   │   │   └── Explicit Mode ✅
│   │   ├── Repository Operations
│   │   │   ├── Clone Management ✅
│   │   │   ├── Branch Creation ✅
│   │   │   ├── Commit Support ✅
│   │   │   ├── Push Support ✅
│   │   │   └── PR Creation ✅
│   │   ├── State Management
│   │   │   ├── State File Creation ✅
│   │   │   ├── Resume Mode ✅
│   │   │   └── Secure Key Hashing ✅
│   │   └── Report Parsing
│   │       ├── Markdown Report Parsing ✅
│   │       ├── Identifier Extraction ✅
│   │       └── Occurrence Tracking ✅
│   ├── Planned Features
│   │   ├── Key Validation
│   │   │   ├── Format Validation 🔄
│   │   │   └── AWS API Testing (Optional) 📋
│   │   ├── Enhanced Verification
│   │   │   ├── Diff Viewing (--verify-changes) 📋
│   │   │   ├── Interactive Confirmation 📋
│   │   │   └── Summary Preview 📋
│   │   ├── Performance Improvements
│   │   │   ├── Parallel Processing (--parallel) 📋
│   │   │   └── Rate Limit Handling 📋
│   │   ├── Error Recovery
│   │   │   ├── Retry Logic with Backoff 📋
│   │   │   ├── Transient vs Permanent Error Detection 📋
│   │   │   └── Automatic Retry for Transient Failures 📋
│   │   ├── Extended Secret Types
│   │   │   ├── GitHub Tokens 📋
│   │   │   ├── API Keys 📋
│   │   │   ├── Username/Password Pairs 📋
│   │   │   └── OAuth Credentials 📋
│   │   ├── Interactive Mode
│   │   │   ├── Repository Selection 📋
│   │   │   ├── Per-Repository Confirmation 📋
│   │   │   └── Preview Before Processing 📋
│   │   ├── Rollback Functionality
│   │   │   ├── Rollback Command (--rollback) 📋
│   │   │   ├── Selective Rollback 📋
│   │   │   └── Rollback Verification 📋
│   │   └── Enhanced Reporting
│   │       ├── JSON Output Format 📋
│   │       ├── Detailed Statistics 📋
│   │       ├── Time Tracking 📋
│   │       └── Per-Repository Status 📋
│   └── Future Enhancements
│       ├── Configuration File Support 📋
│       ├── Cross-File Discovery 📋
│       ├── Multiple Match Handling 📋
│       └── Custom Pattern Definitions 📋
└── Defects
    ├── Open
    │   └── (None)
    ├── Fixed
    │   └── [BUG-1](BUG-1.md) - Validation Order Issue ✅ (Fixed 2026-01-06)
    └── Not Fixable
        └── (None yet)
```

## Legend

- ✅ **Implemented** - Feature is complete and working
- 🔄 **In Progress** - Feature is currently being developed
- 📋 **Planned** - Feature is planned but not yet started
- 🐛 **Bug** - Defect that needs to be fixed

## Feature Categories

### Core Functionality

#### Secret Rotation
- **Single Secret Rotation** ✅ - Rotate individual secrets (AWS Access Key ID)
- **Paired Secret Rotation** ✅ - Rotate paired secrets together (Access Key ID + Secret Access Key)
- **Automatic Discovery** 🔄 - Automatically find paired secrets near primary secrets (Phase 2)
- **Explicit Mode** ✅ - Explicitly specify paired secret identifier

#### Repository Operations
- **Clone Management** ✅ - Clone repositories, reuse existing clones
- **Branch Creation** ✅ - Create timestamped branches for rotations
- **Commit Support** ✅ - Commit changes to branches
- **Push Support** ✅ - Push branches to remote repositories
- **PR Creation** ✅ - Create pull requests via GitHub CLI or API

#### State Management
- **State File Creation** ✅ - Save rotation state to secure files
- **Resume Mode** ✅ - Resume operations from saved state
- **Secure Key Hashing** ✅ - Store key hashes (not plaintext) in state files

#### Report Parsing
- **Markdown Report Parsing** ✅ - Parse trufflehog-analyze-results.py reports
- **Identifier Extraction** ✅ - Extract TOKEN_* and RAW_* identifiers
- **Occurrence Tracking** ✅ - Track all occurrences of secrets across repositories

### Planned Features

#### Key Validation
- **Format Validation** 🔄 - Validate AWS key format before rotation
- **AWS API Testing** 📋 - Optional validation via AWS API (requires credentials)

#### Enhanced Verification
- **Diff Viewing** 📋 - `--verify-changes` option to review changes before committing
- **Interactive Confirmation** 📋 - Confirm each file/repository before processing
- **Summary Preview** 📋 - Show summary of all changes before starting

#### Performance Improvements
- **Parallel Processing** 📋 - `--parallel <N>` to process multiple repositories concurrently
- **Rate Limit Handling** 📋 - Respect GitHub rate limits during parallel operations

#### Error Recovery
- **Retry Logic** 📋 - Exponential backoff retry for network operations
- **Error Categorization** 📋 - Distinguish transient vs permanent errors
- **Automatic Retry** 📋 - Retry transient failures automatically

#### Extended Secret Types
- **GitHub Tokens** 📋 - Support rotating GitHub personal access tokens
- **API Keys** 📋 - Support generic API key rotation
- **Username/Password Pairs** 📋 - Support username/password rotation
- **OAuth Credentials** 📋 - Support OAuth client ID/secret rotation

#### Interactive Mode
- **Repository Selection** 📋 - Interactive selection of repositories to process
- **Per-Repository Confirmation** 📋 - Confirm each repository before processing
- **Preview Before Processing** 📋 - Preview changes before applying

#### Rollback Functionality
- **Rollback Command** 📋 - `--rollback` to undo rotation changes
- **Selective Rollback** 📋 - Rollback specific repositories or all
- **Rollback Verification** 📋 - Verify rollback was successful

#### Enhanced Reporting
- **JSON Output** 📋 - `--output-format json` for automation
- **Detailed Statistics** 📋 - Comprehensive statistics and metrics
- **Time Tracking** 📋 - Track time taken for operations
- **Per-Repository Status** 📋 - Detailed status for each repository

### Future Enhancements
- **Configuration File Support** 📋 - Use config files for key pair mappings
- **Cross-File Discovery** 📋 - Find paired secrets in different files
- **Multiple Match Handling** 📋 - Handle multiple paired secret matches
- **Custom Pattern Definitions** 📋 - User-defined pattern matching

## Defect Categories

### Open Defects

#### BUG-1: Validation Order Issue
- **Priority:** High
- **Severity:** Medium
- **Status:** Open
- **Description:** Script prompts for sensitive key input before validating prerequisites
- **Impact:** Users enter secrets unnecessarily when script will fail
- **See:** [BUG-1.md](BUG-1.md)

### Fixed Defects
- (None yet)

### Not Fixable
- (None yet)

## Related Documentation

- [Design Documents](../design/) - Feature design specifications
- [Planning Documents](../planning/) - Implementation plans
- [Issues](../issues/) - Known issues and workarounds

## Status Tracking

This tree is updated as features are implemented and defects are fixed. See individual defect files for detailed status and resolution information.
