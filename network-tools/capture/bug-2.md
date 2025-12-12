# Bug-2: Linting tools not installed, make lint silently skips

**Status:** Fixed

**Issue:**
The `make lint` target checks for pylint and flake8 but silently skips if they're not installed, providing no way to actually run linting.

**Impact:**
- No code quality checks can be performed
- Silent failures - users don't know linting isn't happening
- Poor developer experience

**Root Cause:**
- Linting tools are optional dependencies but not auto-installed
- No clear path to install them
- Following same pattern as pytest, should auto-install when needed

**Fix:**
- Update Makefile to auto-install pylint and flake8 when running `make lint`
- Follow same pattern as pytest (check if installed, install if missing)
- Provide clear feedback when installing

**Resolution:**
Makefile now auto-installs pylint and flake8 when running `make lint`, following the same pattern as pytest installation.
