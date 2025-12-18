#!/bin/bash
# Install pre-commit hooks
# Copies hooks from hooks/ directory to .git/hooks/

set -euET -o pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
project_root="$(git rev-parse --show-toplevel 2>/dev/null || echo "$script_dir")"
hooks_dir="${project_root}/git/hooks"
git_hooks_dir="${project_root}/.git/hooks"

if [ ! -d "$git_hooks_dir" ]; then
    echo "ERROR: Not a git repository. .git/hooks directory not found." >&2
    exit 1
fi

if [ ! -d "$hooks_dir" ]; then
    echo "ERROR: hooks directory not found: $hooks_dir" >&2
    exit 1
fi

echo "Installing pre-commit hooks..." >&2
echo "  Source: $hooks_dir" >&2
echo "  Target: $git_hooks_dir" >&2

# Install pre-commit hook
if [ -f "${hooks_dir}/pre-commit" ]; then
    cp "${hooks_dir}/pre-commit" "${git_hooks_dir}/pre-commit"
    chmod +x "${git_hooks_dir}/pre-commit"
    echo "  ✓ Installed pre-commit hook" >&2
else
    echo "  ✗ pre-commit hook not found" >&2
    exit 1
fi

# Install commit-msg hook
if [ -f "${hooks_dir}/commit-msg" ]; then
    cp "${hooks_dir}/commit-msg" "${git_hooks_dir}/commit-msg"
    chmod +x "${git_hooks_dir}/commit-msg"
    echo "  ✓ Installed commit-msg hook" >&2
else
    echo "  ✗ commit-msg hook not found" >&2
    exit 1
fi

echo "" >&2
echo "✓ Pre-commit hooks installed successfully" >&2
echo "" >&2
echo "Hooks will now run automatically on:" >&2
echo "  - git commit (pre-commit: checks files)" >&2
echo "  - git commit (commit-msg: checks commit message)" >&2
