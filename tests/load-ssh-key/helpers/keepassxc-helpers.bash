#!/usr/bin/env bash
# KeePassXC test helper functions for load-ssh-key.sh tests

################################################################################
# Mock keepassxc-cli
################################################################################

# Put a mock keepassxc-cli on PATH and register its fake entries.
# load-ssh-key.sh probes "command -v keepassxc-cli" first, so prepending to PATH
# is all that is needed - no hook in the script under test.
#
# Usage: create_mock_keepassxc_cli <master_password> [<entry_path>=<passphrase> ...]
create_mock_keepassxc_cli() {
    local master="$1"
    shift

    local mock_bin="${TEST_TMPDIR}/mockbin"
    mkdir -p "${mock_bin}"
    cp "${TEST_DIR}/helpers/mock-keepassxc-cli.sh" "${mock_bin}/keepassxc-cli"
    chmod 755 "${mock_bin}/keepassxc-cli"

    export MOCK_KEEPASS_MASTER="${master}"
    export MOCK_KEEPASS_ENTRIES="${TEST_TMPDIR}/mock_keepass_entries"
    export MOCK_KEEPASS_LOG="${TEST_TMPDIR}/mock_keepass_calls.log"
    : > "${MOCK_KEEPASS_ENTRIES}"
    : > "${MOCK_KEEPASS_LOG}"

    local pair=""
    for pair in "$@" ; do
        printf '%s\n' "${pair}" >> "${MOCK_KEEPASS_ENTRIES}"
    done

    export PATH="${mock_bin}:${PATH}"
}

# Create a stand-in .kdbx file. Only its existence is checked before
# keepassxc-cli is invoked, and the mock never opens it.
# Usage: create_mock_kdbx [file_name]
create_mock_kdbx() {
    local db_name="${1:-test.kdbx}"
    local db_path="${TEST_TMPDIR}/${db_name}"

    touch "${db_path}"
    echo "${db_path}"
}

# Number of times the mock keepassxc-cli was invoked
mock_keepassxc_call_count() {
    if [ ! -f "${MOCK_KEEPASS_LOG:-}" ] ; then
        echo "0"
        return
    fi

    # grep -c exits 1 on a zero count, so print the count and swallow the status
    grep -c '' "${MOCK_KEEPASS_LOG}" 2>/dev/null || true
}

# Remove the mock from PATH and clear its state
cleanup_mock_keepassxc_cli() {
    if [ -n "${TEST_TMPDIR:-}" ] ; then
        rm -rf "${TEST_TMPDIR}/mockbin" 2>/dev/null || true
        rm -f "${TEST_TMPDIR}/mock_keepass_entries" 2>/dev/null || true
        rm -f "${TEST_TMPDIR}/mock_keepass_calls.log" 2>/dev/null || true
    fi

    unset MOCK_KEEPASS_MASTER
    unset MOCK_KEEPASS_ENTRIES
    unset MOCK_KEEPASS_LOG
    unset LOAD_SSH_KEY_DB_PASSWORD
}
