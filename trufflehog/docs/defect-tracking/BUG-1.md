# BUG-1: Script Prompts for Key Before Validating Prerequisites

**Status:** Fixed  
**Priority:** High  
**Severity:** Medium  
**Reported:** 2026-01-06  
**Fixed:** 2026-01-06  
**Component:** `trufflehog-rotate-aws-key.py`

**Description:**
The script prompts for sensitive AWS key input (via `getpass.getpass()`) before validating that the report file exists and that the identifier is valid in the report. This causes users to enter sensitive secrets unnecessarily when the script will fail immediately after due to missing files or invalid identifiers.

**Error Message:**
```
Enter new AWS key (input will be hidden):
ERROR: Report file not found: /Users/lblackb/data/git/radioactive/trufflehog/2026-01-05_analysis_20260106_024359.md
```

**Steps to Reproduce:**
1. Run the script with a non-existent report file:
   ```bash
   ./trufflehog-rotate-aws-key.py \
       -i RAW_c25c34ee_bb9c4917 \
       -r ~/data/git/radioactive/trufflehog/2026-01-05_analysis_20260106_024359.md \
       --paired-secret \
       --mode dry-run \
       --debug
   ```
2. Script prompts: "Enter new AWS key (input will be hidden):"
3. User enters key (sensitive data entered unnecessarily)
4. Script immediately fails with: "ERROR: Report file not found: ..."

**Expected Behavior:**
- Script should validate report file exists FIRST
- Script should parse report and validate identifier exists
- Script should THEN prompt for new key only after all prerequisites are validated
- User should see error about missing file BEFORE being prompted for sensitive input

**Actual Behavior:**
- Script prompts for new AWS key immediately
- User enters sensitive secret
- Script then validates report file and fails
- Sensitive data was entered unnecessarily

**Root Cause:**
The code flow in `main()` function has validation logic (report file existence, identifier validation) placed AFTER the key prompting logic. The order should be:
1. Validate prerequisites (report file, identifier)
2. Then prompt for sensitive input (keys)

**Environment:**
- Script: `trufflehog-rotate-aws-key.py`
- Python Version: 3.x
- OS: macOS (darwin 24.6.0)
- Mode: Any mode (dry-run, commit)

**Files Affected:**
- `trufflehog/scripts/trufflehog-rotate-aws-key.py` - Lines ~1697-1722 (validation order)

**Impact:**
- **Security/UX:** Users enter sensitive secrets unnecessarily when script will fail
- **User Experience:** Poor UX - prompts for input before validating prerequisites
- **Security Best Practice:** Should validate all prerequisites before requesting sensitive input

**Solution Required:**
1. Move report file validation to occur BEFORE key prompting
2. Move identifier validation to occur BEFORE key prompting
3. Only prompt for keys after all prerequisites are validated
4. Ensure same validation order for paired secret mode

**Solution Implemented:**
1. ✅ Moved report file validation to occur BEFORE key prompting
2. ✅ Moved identifier validation to occur BEFORE key prompting
3. ✅ Added comment documenting the fix (BUG-1 reference)
4. ✅ Key prompting now only occurs after all prerequisites are validated

**Files Modified:**
- `trufflehog/scripts/trufflehog-rotate-aws-key.py` - Lines ~1697-1742 (reordered validation logic)

**Code Changes:**
- Moved report file existence check (lines 1700-1712) to execute before key prompting
- Moved report parsing and identifier validation (lines 1714-1722) to execute before key prompting
- Key prompting logic (lines 1724-1742) now executes only after prerequisites are validated
- Added comment: "Validate prerequisites BEFORE prompting for sensitive input (keys)"

**Verification:**
✅ Fix verified - Script now validates report file and identifier BEFORE prompting for sensitive key input. Users will see errors about missing files or invalid identifiers immediately, without being prompted for secrets.

**Before Fix:**
```
Enter new AWS key (input will be hidden):
ERROR: Report file not found: ...
```

**After Fix:**
```
ERROR: Report file not found: ...
```

**Additional Notes:**
- This affects both single-secret and paired-secret modes
- Paired secret prompting already validates paired secret identifier before prompting (correct order)
- This fix improves UX and follows security best practices - validate prerequisites before requesting sensitive input
