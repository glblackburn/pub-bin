# Design Document Analysis - Consistency Review

**Last Updated**: 2025-12-04  
**Status**: Most issues resolved, one deferred decision remains

---

## Table of Contents

- [Unresolved / Deferred Issues](#unresolved--deferred-issues)
- [Decisions Made](#decisions-made)
  - [1. Detector Type Display Logic](#-1-detector-type-display-logic---resolved)
  - [2. Anchor ID Format](#-2-anchor-id-format---resolved)
  - [3. Data Structure](#-3-data-structure---resolved)
  - [4. Repository Name Extraction](#-4-repository-name-extraction---resolved)
  - [5. Multiple Detector Types Per Token](#-5-multiple-detector-types-per-token---resolved)
  - [6. Line Number Extraction](#-6-line-number-extraction---resolved)
  - [7. Token Details Section](#-7-token-details-section---resolved)
  - [8. Branch Detection](#-8-branch-detection---resolved)
  - [9. Repository Summary Table](#-9-repository-summary-table---resolved)
  - [12. Missing Detector Type Handling](#-12-missing-detector-type-handling---resolved)
  - [13. Repository URL Caching](#-13-repository-url-caching---resolved)
  - [14. Error Handling](#-14-error-handling---resolved)
- [Consistency Issues Found](#consistency-issues-found)
- [Outstanding Issues / Questions](#outstanding-issues--questions)
- [Summary of Outstanding Questions](#summary-of-outstanding-questions)

---

## UNRESOLVED / DEFERRED ISSUES

### 10. File Summary Table - Missing Detector Type

**Status**: ⏸️ DEFERRED - Wait until working version to decide

**Issue**: File summary table doesn't include detector type.

**Question**: Should the file summary table also include detector types found in each file?

**Options**:
- A) Add detector type column
- B) Show multiple detector types if file has tokens with different types
- C) Keep it simple, no detector type

**Decision**: Defer decision until after initial working version is complete. See "Future Considerations" section below.

**Rationale for Deferral**: 
- Wait until we have a working version to see if detector type in file table adds value
- May be redundant if detector type is already shown in token details
- Can be added as enhancement after initial implementation

---

## DECISIONS MADE

### ✅ 1. Detector Type Display Logic - RESOLVED

**Decision**: The same token should NOT appear with different detector types. This is an **ERROR condition** that must be flagged.

- If the same token is found with multiple detector types, flag as ERROR
- Report the error with token and conflicting detector types
- Continue processing but mark token with error flag
- Show error indicator in output (e.g., "ERROR: Multiple detector types")

**Updated in design**: Error handling section now includes this validation.

---

### ✅ 2. Anchor ID Format - RESOLVED

**Decision**: Use hyphens consistently for markdown compatibility.

- Format: `token-abc123-def456` (lowercase, hyphens)
- Function: `create_token_anchor_id()` converts `TOKEN_abc123_def456` → `token-abc123-def456`

**Updated in design**: All examples and function descriptions use hyphens.

---

### ✅ 3. Data Structure - RESOLVED

**Decision**: Single `detector_type` field with error flag.

- Changed from `detector_types` (list) to `detector_type` (string)
- Added `detector_type_error` boolean flag
- If multiple types found, set error flag to true

**Updated in design**: Data structure section reflects single detector_type field.

---

### ✅ 4. Repository Name Extraction - RESOLVED

**Decision**: Extract repository name from `file://` URI path (last component).

- Input: `file:///path/to/repos/example-repo`
- Output: `example-repo` (last component of path)
- No git remote access needed - only use trufflehog output

**Updated in design**: Parsing strategy and URL generation sections updated.

---

### ✅ 5. Multiple Detector Types Per Token - RESOLVED

**Decision**: This is an ERROR condition, not a valid scenario.

- Same token with different detector types = ERROR
- Must be flagged and reported
- See issue #1 above

**Updated in design**: Error handling and validation sections updated.

---

### ✅ 6. Line Number Extraction - RESOLVED

**Decision**: Line number is in separate "Line:" field, not embedded in file path.

- From actual trufflehog output: `Line: 55` (separate field)
- File path: `aws/lambdas/file.py` (no line number)
- Extract from "Line:" field directly

**Updated in design**: Information extraction section updated with actual format.

---

### ✅ 11. Parsing Strategy - RESOLVED

**Decision**: We now have the actual trufflehog output format.

- Actual format documented with example
- Field order: Detector Type → Raw result → File → Line → Repository
- Parsing strategy updated to handle actual format

**Updated in design**: Input file format section shows actual example.

---

### ✅ 7. Token Details Section - RESOLVED

**Decision**: Add detector type to token detail section summary line.

- Added `**Detector Type:**` to token detail section header
- Consistent with summary table display
- Shows detector type alongside Occurrences, Repositories, Files

**Updated in design**: Token detail sections now include detector type in summary line.

---

### ✅ 8. Branch Detection - RESOLVED

**Decision**: Accept that URLs may break if repo state changed.

- Try to detect current branch from local repo if Repository path exists locally
- Allow override via `--branch` flag
- Document that URLs may be broken if repository state changed
- This is acceptable given we only have `file://` paths, not git remotes

**Updated in design**: Branch detection strategy documented with limitations.

---

### ✅ 9. Repository Summary Table - RESOLVED

**Decision**: Add clickable repository names linking to GitHub repo URLs.

- Repository names in summary table are clickable links
- Format: `[repo-name](https://github.com/{org}/{repo-name})`
- Uses org from repo-map or default --org parameter

**Updated in design**: Repository summary table shows clickable links.

---

### ✅ 12. Missing Detector Type Handling - RESOLVED

**Decision**: Show as "Unknown", continue processing.

- If token occurrence doesn't have detector type, show as "Unknown"
- Continue processing (don't skip tokens)
- Display "Unknown" in summary table and token details
- Log warning in verbose mode

**Updated in design**: Error handling section includes missing detector type handling.

---

### ✅ 13. Repository URL Caching - RESOLVED

**Decision**: Cache branch lookups for efficiency.

- Cache repository branch lookups to avoid repeated git commands
- Use branch_cache dictionary to store results
- Check cache before running git commands

**Updated in design**: `detect_branch()` function includes caching.

---

### ✅ 14. Error Handling - RESOLVED

**Decision**: Multiple detector types for same token is an ERROR.

- Added to error handling section
- Report error, continue processing, mark with error flag

**Updated in design**: Error handling section includes this case.

---

## Consistency Issues Found

### ~~1. Detector Type Display Logic - RESOLVED~~ ✅

**Status**: RESOLVED - Multiple detector types for same token is an ERROR condition.

---

### ~~2. Anchor ID Format - RESOLVED~~ ✅

**Status**: RESOLVED - Using hyphens consistently throughout design.

---

### ~~3. Data Structure - RESOLVED~~ ✅

**Status**: RESOLVED - Changed to single `detector_type` field with error flag.

---

### ~~4. Repository Name Extraction - RESOLVED~~ ✅

**Status**: RESOLVED - Extract from `file://` URI path (last component). No git remote access needed.

---

### ~~5. Multiple Detector Types Per Token - RESOLVED~~ ✅

**Status**: RESOLVED - This is an ERROR condition, not a valid scenario.

---

### ~~6. Line Number Extraction - RESOLVED~~ ✅

**Status**: RESOLVED - Line number is in separate "Line:" field (confirmed from actual output).

---

### ~~7. Token Details Section - RESOLVED~~ ✅

**Status**: RESOLVED - Detector type added to summary line.

---

### ~~8. Branch Detection - RESOLVED~~ ✅

**Status**: RESOLVED - Accept that URLs may break if repo state changed.

---

### ~~9. Repository Summary Table - RESOLVED~~ ✅

**Status**: RESOLVED - Add clickable repository names linking to GitHub repo URLs.

---

### 10. File Summary Table - Missing Detector Type

**Issue**: File summary table (lines 239-242) doesn't include detector type.

**Question**: Should the file summary table also include detector types found in each file?

**Recommendation**: Consider adding detector type column, or at least document whether it should be included.

---

### ~~11. Parsing Strategy - RESOLVED~~ ✅

**Status**: RESOLVED - Actual trufflehog output format documented with example.

---

### 12. Missing Detector Type Handling

**Issue**: What if a token occurrence doesn't have a detector type?

**Question**: 
- Should we skip tokens without detector types?
- Show as "Unknown" or "N/A"?
- Continue processing but mark as missing?

**Recommendation**: Show as "Unknown" in the summary table, continue processing. Document this behavior.

---

### 13. Repository URL Caching

**Issue**: No mention of caching repository URL lookups.

**Question**: If the same repository appears in multiple files, should we:
- Look up the git remote once and cache it?
- Or look it up every time (inefficient)?

**Recommendation**: Cache repository URL lookups to avoid repeated git commands for the same repo.

---

### 14. Error Handling - Missing Detector Type

**Issue**: Error handling section doesn't mention what to do if detector type is missing.

**Question**: Should missing detector type be treated as an error, warning, or silently handled?

**Recommendation**: Add to error handling section - treat as warning, show "Unknown" in output.

---

## Recommendations Summary

1. **Clarify detector type display logic**: Show all unique types comma-separated
2. **Fix anchor ID format**: Use hyphens consistently
3. **Clarify repository name extraction**: Extract from git URL or last path component
4. **Add detector type to token detail summary**: Include in header for consistency
5. **Document parsing order**: Specify expected field order in trufflehog output
6. **Handle missing detector types**: Show as "Unknown"
7. **Add repository URL caching**: Cache lookups for efficiency
8. **Enhance repository/file summary tables**: Add links and consider detector type columns
9. **Document branch detection limitations**: URLs may break if repo state changed

---

---

## OUTSTANDING ISSUES / QUESTIONS

### ✅ 7. Token Details Section - RESOLVED

**Status**: RESOLVED - Detector type added to summary line.

**Decision**: Added `**Detector Type:**` to the token detail section header for consistency with summary table.

**Updated in design**: Token detail sections now include detector type in summary line.

---

### ✅ 8. Branch Detection - RESOLVED

**Status**: RESOLVED - Accept that URLs may break if repo state changed.

**Decision**: 
- Try to detect current branch from local repo if Repository path exists locally
- Allow override via `--branch` flag
- Document that URLs may be broken if repository state changed
- This is acceptable given we only have `file://` paths, not git remotes

**Updated in design**: 
- Branch detection strategy documented
- Limitation documented in error handling section
- Help text updated to mention potential URL breakage

---

### ✅ 9. Repository Summary Table - RESOLVED

**Status**: RESOLVED - Add clickable repository names linking to GitHub repo URLs.

**Decision**: Repository names in the summary table are clickable links to GitHub repository URLs.

**Format**: `[repo-name](https://github.com/{org}/{repo-name})`

**Updated in design**: 
- Repository summary table shows clickable links
- Function `format_repository_summary_table()` creates links using org from repo-map or default --org
- Consistent with file links in token detail sections

---


### ✅ 12. Missing Detector Type Handling - RESOLVED

**Status**: RESOLVED - Show as "Unknown", continue processing.

**Decision**: 
- If a token occurrence doesn't have a detector type, show as "Unknown"
- Continue processing (don't skip tokens)
- Display "Unknown" in summary table and token details
- Log warning in verbose mode

**Updated in design**: 
- Error handling section includes missing detector type handling
- Data structure includes `detector_type_missing` flag
- Function descriptions updated

---

### ✅ 13. Repository URL Caching - RESOLVED

**Status**: RESOLVED - Cache branch lookups for efficiency.

**Decision**: 
- Cache repository branch lookups to avoid repeated git commands for the same repo
- Use branch_cache dictionary to store results
- Check cache before running git commands

**Updated in design**: 
- `detect_branch()` function signature includes `branch_cache` parameter
- Documented caching strategy in function description

---

## Summary of Outstanding Questions

1. ~~**Token Detail Header**: Add detector type to summary line?~~ ✅ RESOLVED
2. ~~**Branch Detection**: Accept that URLs may break if repo state changed?~~ ✅ RESOLVED
3. ~~**Repository Table**: Add clickable links?~~ ✅ RESOLVED
4. **File Table**: Add detector type column? ⏸️ DEFERRED (See "Unresolved/Deferred Issues" at top)
5. ~~**Missing Detector Type**: Show "Unknown" or skip?~~ ✅ RESOLVED
6. ~~**URL Caching**: Cache git lookups for efficiency?~~ ✅ RESOLVED

**Note**: All issues except File Summary Table detector type have been resolved. See "Unresolved/Deferred Issues" section at the top of this document for the deferred decision.
