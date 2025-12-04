# Recommendation: Remove All Real Key Name References

## Status: ✅ COMPLETED

All real key names have been removed from the codebase and replaced with generic placeholders.

### Files Updated (All Completed)

1. **`tests/load-ssh-key/KEY-CONFIG-RECOMMENDATION.md`**
   - ✅ **Status**: Completed - Replaced key names with generic placeholders

2. **`tests/load-ssh-key/archive/TESTING-PLAN-load-ssh-key-k-option.md`**
   - ✅ **Status**: Completed - All key names replaced with generic placeholders

3. **`tips-and-tricks.md`**
   - ✅ **Status**: Completed - Replaced with generic `id_ed25519` and placeholder

## Recommended Actions

### Option 1: Replace with Placeholders (Recommended)

**For `archive/TESTING-PLAN-load-ssh-key-k-option.md`:**
- ✅ Completed - Replaced all key names with generic placeholders:
  - `your-key-no-passphrase.pem` (example key without passphrase)
  - `your-key-with-passphrase` (example key with passphrase)
  - `your-second-key` (example additional test key)
  - `your-third-key` (example additional test key)

**For `tips-and-tricks.md`:**
- ✅ Completed - Replaced with generic `id_ed25519` or `your-ssh-key`

**For `KEY-CONFIG-RECOMMENDATION.md`:**
- ✅ Completed - Replaced key names in "Current Problem" section with generic placeholders

### Option 2: Mark as Historical/Archive

**For `archive/TESTING-PLAN-load-ssh-key-k-option.md`:**
- Add header note: "This is a historical planning document. Key names are examples only."
- Or move to a deeper archive (e.g., `archive/historical/`)

**For `tips-and-tricks.md`:**
- Replace with generic example

### Option 3: Remove Entirely

**For `archive/TESTING-PLAN-load-ssh-key-k-option.md`:**
- If no longer needed, delete it
- It's already in `archive/` so it's not actively used

## Detailed File Analysis

### 1. `archive/TESTING-PLAN-load-ssh-key-k-option.md`

**References found:**
- ✅ All references have been replaced with generic placeholders

**Total**: All ~20 references replaced

**Status**: ✅ Completed - All key names replaced with generic placeholders

### 2. `tips-and-tricks.md`

**References found:**
- ✅ All references have been replaced

**Status**: ✅ Completed - Replaced with generic `id_ed25519` and `your-ssh-key` placeholder

### 3. `KEY-CONFIG-RECOMMENDATION.md`

**References found:**
- ✅ All references have been replaced with generic placeholders

**Status**: ✅ Completed - Replaced key names with generic examples in "Current Problem" section

## Implementation Plan

### Step 1: Update Archive Documentation

✅ **Completed** - Replaced all key names in `archive/TESTING-PLAN-load-ssh-key-k-option.md` with generic placeholders:
- `your-key-no-passphrase.pem` (example key without passphrase)
- `your-key-with-passphrase` (example key with passphrase)
- `your-second-key` (example additional test key)
- `your-third-key` (example additional test key)

### Step 2: Update Tips File

✅ **Completed** - Updated `tips-and-tricks.md`:
- Replaced with generic `id_ed25519` and added comment with `your-ssh-key` placeholder

### Step 3: Verify No Other References

✅ **Completed** - All real key names have been removed from tracked files. Remaining references are only in this documentation file (REMOVE-KEY-NAMES-RECOMMENDATION.md) which documents the cleanup process.

### Step 4: Update Git History (Optional)

If you want to remove from git history entirely:
- Use `git filter-branch` or `git filter-repo` (more modern)
- **Warning**: This rewrites history and requires force push
- **Recommendation**: Only do this if the repository is private and you understand the implications

## Summary

**Files to Update:**
1. ✅ `archive/TESTING-PLAN-load-ssh-key-k-option.md` - Replace all key names with placeholders
2. ✅ `tips-and-tricks.md` - ✅ Completed - Replaced with generic example
3. ✅ `KEY-CONFIG-RECOMMENDATION.md` - Replace key names with generic placeholders

**Files Already Clean:**
- ✅ All unit test files (`.bats`)
- ✅ All archive test scripts (`.sh`) - now use config
- ✅ All helper scripts
- ✅ Main script (`load-ssh-key.sh`)

**Git History:**
- Key names exist in commit history but are in archived/test files
- Consider if history cleanup is needed (only if repository is private)

## Priority

**High Priority:**
- `archive/TESTING-PLAN-load-ssh-key-k-option.md` - Many references, should be generic

**Medium Priority:**
- `tips-and-tricks.md` - Single reference, but in general documentation

**Low Priority:**
- Git history cleanup (only if needed for security/compliance)
