#!/usr/bin/env bash
# setup-path.sh — extend PATH with every pub-bin subdir that holds runnable
# scripts.  Intended to be SOURCED from ~/.bash_profile with a single line:
#
#     . "${HOME}/data/lblackb/git/pub-bin/setup-path.sh"
#
# Discovery rule
# --------------
# Any directory under pub-bin (up to 4 levels deep) that contains at least
# one executable *.sh or *.py file is added to PATH.  The pub-bin root
# itself is always added.
#
# Denylist
# --------
# Directories whose path matches a known internal-only pattern are skipped:
#   .git/                 git internals
#   tests/, test_hooks/   test code and fixtures
#   hooks/                git hook scripts (invoked by git, not the user)
#   config/               sourceable helpers (e.g. config/config.sh)
#   archive/              retired scripts
#   credential-loaders/   importable Python package, not commands
#
# Add new tool subdirs anywhere under pub-bin and they get picked up the
# next time your shell starts.  To intentionally keep a subdir off PATH,
# place it under one of the denylisted names above (or extend the denylist).
#
# Idempotent: re-sourcing this script does not duplicate PATH entries.

# Do not 'set -e' — this file is sourced and must not abort the parent shell.

_pub_bin_root="${HOME}/data/lblackb/git/pub-bin"
if [ ! -d "${_pub_bin_root}" ] ; then
    unset _pub_bin_root
    return 0 2>/dev/null || exit 0
fi

# Substring patterns that disqualify a directory.  Matched as path segments
# (a leading or interior '/<name>/' or trailing '/<name>').
_pub_bin_deny_re='/(\.git|tests?|test_hooks|hooks|config|archive|credential-loaders)(/|$)'

# Append a directory to PATH if it is not already present.
_pub_bin_add() {
    case ":${PATH}:" in
        *":$1:"*) ;;
        *) PATH="${PATH}:$1" ;;
    esac
}

# Always include the pub-bin root itself.
_pub_bin_add "${_pub_bin_root}"

# Auto-discover every subdir that contains at least one executable *.sh or
# *.py file, skipping anything matched by the denylist.  -maxdepth 4 is
# generous enough for the current tree shape (e.g. trufflehog/scripts).
while IFS= read -r _pub_bin_dir ; do
    [ -z "${_pub_bin_dir}" ] && continue
    if [[ "${_pub_bin_dir}" =~ ${_pub_bin_deny_re} ]] ; then
        continue
    fi
    _pub_bin_add "${_pub_bin_dir}"
done < <(
    find "${_pub_bin_root}" -mindepth 1 -maxdepth 4 -type f \
        \( -name '*.sh' -o -name '*.py' \) -perm -u+x -print0 2>/dev/null \
        | xargs -0 -n1 dirname 2>/dev/null \
        | sort -u
)

export PATH

unset _pub_bin_root _pub_bin_deny_re _pub_bin_dir
unset -f _pub_bin_add
