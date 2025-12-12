# Bug-1: Tests not run before commit

**Status:** Fixed

**Issue:**
Tests were not run before committing the implementation. The Makefile assumes pytest is installed but doesn't check for it or provide installation instructions.

**Impact:**
- `make test` fails with "pytest: command not found"
- No verification that the implementation actually works
- Poor developer experience

**Root Cause:**
- Assumed pytest would be available
- No dependency checking in Makefile
- No installation instructions or automatic installation

**Fix:**
- Updated Makefile to check for pytest and provide installation instructions
- Added dependency checking before running tests
- Added install-deps target to install pytest if missing

**Resolution:**
Makefile now checks for pytest and provides clear error messages with installation instructions if missing.
