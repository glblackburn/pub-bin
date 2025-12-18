#!/bin/bash
# Verify that git hooks are working correctly
# Tests both pre-commit and commit-msg hooks

set -e

echo "=== Git Hooks Verification ==="
echo ""

# Check if hooks are installed
project_root="$(git rev-parse --show-toplevel)"
if [ ! -f "${project_root}/.git/hooks/pre-commit" ]; then
    echo "❌ ERROR: pre-commit hook not found"
    echo "   Run: ./git/install-hooks.sh"
    exit 1
fi

if [ ! -f "${project_root}/.git/hooks/commit-msg" ]; then
    echo "❌ ERROR: commit-msg hook not found"
    echo "   Run: ./git/install-hooks.sh"
    exit 1
fi

echo "✅ Hooks are installed"
echo ""

# Get project root
project_root="$(git rev-parse --show-toplevel)"
test_dir="${project_root}/git/test_hooks"

# Create test directory if it doesn't exist
mkdir -p "$test_dir"

# Test 1: Pre-commit hook blocks file with AWS key
echo "Test 1: Pre-commit hook blocks file with AWS key..."
echo "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE" > "${test_dir}/test_hook_verify.py"
git add "${test_dir}/test_hook_verify.py" 2>/dev/null || true

if git commit -m "Test: verify hooks" 2>&1 | grep -q "contains sensitive data"; then
    echo "   ✅ PASS: File with AWS key was blocked"
else
    echo "   ❌ FAIL: File with AWS key was NOT blocked"
    git reset HEAD "${test_dir}/test_hook_verify.py" 2>/dev/null || true
    rm -f "${test_dir}/test_hook_verify.py"
    exit 1
fi

git reset HEAD "${test_dir}/test_hook_verify.py" 2>/dev/null || true
rm -f "${test_dir}/test_hook_verify.py"

# Test 2: Commit-msg hook blocks commit message with AWS key
echo ""
echo "Test 2: Commit-msg hook blocks commit message with AWS key..."
echo "def test(): pass" > "${test_dir}/test_hook_verify_clean.py"
git add "${test_dir}/test_hook_verify_clean.py" 2>/dev/null || true

if git commit -m "Added AWS key: AKIAIOSFODNN7EXAMPLE" 2>&1 | grep -q "Commit message contains sensitive data"; then
    echo "   ✅ PASS: Commit message with AWS key was blocked"
else
    echo "   ❌ FAIL: Commit message with AWS key was NOT blocked"
    git reset HEAD "${test_dir}/test_hook_verify_clean.py" 2>/dev/null || true
    rm -f "${test_dir}/test_hook_verify_clean.py"
    exit 1
fi

git reset HEAD "${test_dir}/test_hook_verify_clean.py" 2>/dev/null || true
rm -f "${test_dir}/test_hook_verify_clean.py"

# Test 3: Clean commit is allowed
echo ""
echo "Test 3: Clean commit is allowed..."
echo "def test(): pass" > "${test_dir}/test_hook_verify_clean2.py"
git add "${test_dir}/test_hook_verify_clean2.py" 2>/dev/null || true

if git commit -m "Test: verify hooks work" 2>&1 | grep -q "\[.*\] Test: verify hooks work"; then
    echo "   ✅ PASS: Clean commit was allowed"
    git reset HEAD~1 --hard 2>/dev/null || true
else
    echo "   ❌ FAIL: Clean commit was blocked (unexpected)"
    git reset HEAD "${test_dir}/test_hook_verify_clean2.py" 2>/dev/null || true
    rm -f "${test_dir}/test_hook_verify_clean2.py"
    exit 1
fi

rm -f "${test_dir}/test_hook_verify_clean2.py"

echo ""
echo "=== All Tests Passed ==="
echo "✅ Git hooks are working correctly!"
