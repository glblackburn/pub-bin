#!/usr/bin/env bash
# SSH_ASKPASS helper for load-ssh-key.sh
#
# ssh-add execs this script (with the prompt text as $1) when
# SSH_ASKPASS_REQUIRE=force is set.  The passphrase arrives in the
# LOAD_SSH_KEY_PASSPHRASE environment variable, which load-ssh-key.sh sets as a
# per-command assignment on the ssh-add invocation only -- it is never exported
# into the caller's shell.  Nothing here is logged, echoed to a tty, or written
# to disk.
#
# There is deliberately no getopts/-h block: ssh-add passes the prompt string as
# $1, so option parsing would be actively wrong.

set -euET -o pipefail

script_name=$(basename $0)

################################################################################
# Style Conventions
################################################################################
# - Use ${variable} braces for all variable references
# - Use ${HOME} instead of ~
# - Use $(command) instead of backticks for command substitution
################################################################################

################################################################################
# main script logic
################################################################################
if [[ -z "${LOAD_SSH_KEY_PASSPHRASE:-}" ]] ; then
    echo "Error: ${script_name}: LOAD_SSH_KEY_PASSPHRASE is not set" >&2
    exit 1
fi

# ssh-add reads one line and strips the trailing newline
printf '%s\n' "${LOAD_SSH_KEY_PASSPHRASE}"
exit 0
