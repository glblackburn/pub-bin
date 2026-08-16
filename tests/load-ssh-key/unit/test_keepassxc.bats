#!/usr/bin/env bats
# Test file for load-ssh-key.sh KeePassXC passphrase lookup

load '../test_helper.bash'
load '../helpers/keepassxc-helpers.bash'

################################################################################
# Unit Test Setup
################################################################################

# Test output directory for saving test results (shared across all tests in this file)
TEST_OUTPUT_DIR=""

# Master password used by every mock database in this file
MOCK_MASTER="mock-master-password"

################################################################################
# Test Options and Syntax
################################################################################

@test "load-ssh-key.sh: help lists the KeePassXC options" {
    run_load_ssh_key -h
    assert_success
    assert_output_contains "-D <keepass_db>"
    assert_output_contains "-G <group>"
    assert_output_contains "-N"
    assert_output_contains "KeePassXC"
}

@test "load-ssh-key-askpass.sh: has valid bash syntax" {
    run bash -n "${PROJECT_ROOT}/load-ssh-key-askpass.sh"
    assert_success
}

@test "load-ssh-key-askpass.sh: prints the passphrase from the environment" {
    run env LOAD_SSH_KEY_PASSPHRASE="abc123" "${PROJECT_ROOT}/load-ssh-key-askpass.sh" "Enter passphrase:"
    assert_success
    [ "$output" = "abc123" ] || {
        echo "Expected output 'abc123', got: ${output}" >&2
        return 1
    }
}

@test "load-ssh-key-askpass.sh: fails when the passphrase is not set" {
    run env -u LOAD_SSH_KEY_PASSPHRASE "${PROJECT_ROOT}/load-ssh-key-askpass.sh" "Enter passphrase:"
    assert_failure
    assert_output_contains "LOAD_SSH_KEY_PASSPHRASE is not set"
}

################################################################################
# Test Fallback When KeePassXC Is Not Configured
################################################################################

@test "load-ssh-key.sh: unconfigured KeePassXC does not change behavior" {
    kill_all_ssh_agents
    local test_key=$(create_test_ssh_key "kp_unconfigured")

    run_load_ssh_key -k "${test_key}" -v

    assert_success
    assert_output_not_contains "Using KeePassXC passphrase"
    assert_output_not_contains "No KeePassXC entry found"
    assert_output_contains "KEEPASS_ENABLED=\\[false\\]"
}

################################################################################
# Test Passphrase Lookup
################################################################################

@test "load-ssh-key.sh -D: loads a passphrase-protected key from KeePassXC" {
    kill_all_ssh_agents
    local test_key=$(create_test_ssh_key "kp_protected" "testpass123")
    local kdbx=$(create_mock_kdbx)
    create_mock_keepassxc_cli "${MOCK_MASTER}" "kp_protected=testpass123"
    export LOAD_SSH_KEY_DB_PASSWORD="${MOCK_MASTER}"

    run_load_ssh_key -k "${test_key}" -D "${kdbx}" -v

    assert_success
    assert_output_contains "Using KeePassXC passphrase for: kp_protected"

    # The key really is in the agent
    run_load_ssh_key -l
    assert_success
    assert_output_contains "test@example.com"

    cleanup_mock_keepassxc_cli
}

@test "load-ssh-key.sh -G: finds the entry inside a KeePassXC group" {
    kill_all_ssh_agents
    local test_key=$(create_test_ssh_key "kp_grouped" "testpass123")
    local kdbx=$(create_mock_kdbx)
    create_mock_keepassxc_cli "${MOCK_MASTER}" "ssh-keys/kp_grouped=testpass123"
    export LOAD_SSH_KEY_DB_PASSWORD="${MOCK_MASTER}"

    run_load_ssh_key -k "${test_key}" -D "${kdbx}" -G "ssh-keys" -v

    assert_success
    assert_output_contains "entry_path=\\[ssh-keys/kp_grouped\\]"
    assert_output_contains "Using KeePassXC passphrase for: kp_grouped"

    cleanup_mock_keepassxc_cli
}

@test "load-ssh-key.sh -G: retries at the database root when the group misses" {
    kill_all_ssh_agents
    local test_key=$(create_test_ssh_key "kp_root" "testpass123")
    local kdbx=$(create_mock_kdbx)
    # Entry is filed at the root even though a group was requested
    create_mock_keepassxc_cli "${MOCK_MASTER}" "kp_root=testpass123"
    export LOAD_SSH_KEY_DB_PASSWORD="${MOCK_MASTER}"

    run_load_ssh_key -k "${test_key}" -D "${kdbx}" -G "ssh-keys" -v

    assert_success
    assert_output_contains "retrying entry_path=\\[kp_root\\]"
    assert_output_contains "Using KeePassXC passphrase for: kp_root"

    cleanup_mock_keepassxc_cli
}

@test "load-ssh-key.sh: unprotected keys never consult KeePassXC" {
    kill_all_ssh_agents
    local test_key=$(create_test_ssh_key "kp_plain")
    local kdbx=$(create_mock_kdbx)
    create_mock_keepassxc_cli "${MOCK_MASTER}" "kp_plain=unused"
    export LOAD_SSH_KEY_DB_PASSWORD="${MOCK_MASTER}"

    run_load_ssh_key -k "${test_key}" -D "${kdbx}" -v

    assert_success
    assert_output_not_contains "Using KeePassXC passphrase"
    [ "$(mock_keepassxc_call_count)" -eq 0 ] || {
        echo "Expected 0 keepassxc-cli calls, got $(mock_keepassxc_call_count)" >&2
        cat "${MOCK_KEEPASS_LOG}" >&2
        return 1
    }

    cleanup_mock_keepassxc_cli
}

################################################################################
# Test Failure Handling
################################################################################

@test "load-ssh-key.sh: missing KeePassXC entry falls back and reports an error" {
    kill_all_ssh_agents
    local test_key=$(create_test_ssh_key "kp_missing" "testpass123")
    local kdbx=$(create_mock_kdbx)
    create_mock_keepassxc_cli "${MOCK_MASTER}" "some-other-entry=testpass123"
    export LOAD_SSH_KEY_DB_PASSWORD="${MOCK_MASTER}"

    run_load_ssh_key -k "${test_key}" -D "${kdbx}"

    # The interactive fallback cannot succeed without a tty, so the key fails to
    # load - which must be reported (error_count propagates out of the loop).
    assert_failure
    assert_output_contains "No KeePassXC entry found for: kp_missing"
    assert_output_contains "Failed to load 1 key"

    cleanup_mock_keepassxc_cli
}

@test "load-ssh-key.sh: wrong master password falls back without hanging" {
    kill_all_ssh_agents
    local plain_key=$(create_test_ssh_key "kp_plain_after_bad_master")
    local kdbx=$(create_mock_kdbx)
    create_mock_keepassxc_cli "${MOCK_MASTER}" "kp_protected=testpass123"
    export LOAD_SSH_KEY_DB_PASSWORD="definitely-not-the-master-password"

    local protected_key=$(create_test_ssh_key "kp_protected" "testpass123")

    run_load_ssh_key -D "${kdbx}"

    assert_output_contains "LOAD_SSH_KEY_DB_PASSWORD did not unlock"
    assert_output_contains "Falling back to interactive ssh-add passphrase prompts"

    # The unprotected key in the same run still loads
    run_load_ssh_key -l
    assert_output_contains "test@example.com"

    cleanup_mock_keepassxc_cli
}

@test "load-ssh-key.sh -D: missing database file is a hard error" {
    kill_all_ssh_agents

    run_load_ssh_key -D "${TEST_TMPDIR}/does-not-exist.kdbx"

    assert_failure
    assert_output_contains "KeePassXC database does not exist"
}

@test "load-ssh-key.sh -N: skips KeePassXC entirely" {
    kill_all_ssh_agents
    local test_key=$(create_test_ssh_key "kp_disabled" "testpass123")
    local kdbx=$(create_mock_kdbx)
    create_mock_keepassxc_cli "${MOCK_MASTER}" "kp_disabled=testpass123"
    export LOAD_SSH_KEY_DB_PASSWORD="${MOCK_MASTER}"

    run_load_ssh_key -k "${test_key}" -D "${kdbx}" -N -v

    assert_output_contains "KeePassXC disabled by -N"
    assert_output_not_contains "Using KeePassXC passphrase"
    [ "$(mock_keepassxc_call_count)" -eq 0 ] || {
        echo "Expected 0 keepassxc-cli calls, got $(mock_keepassxc_call_count)" >&2
        return 1
    }

    cleanup_mock_keepassxc_cli
}

################################################################################
# Test Secret Hygiene
################################################################################

@test "load-ssh-key.sh -v: never prints the passphrase or master password" {
    kill_all_ssh_agents
    local test_key=$(create_test_ssh_key "kp_secret_check" "testpass123")
    local kdbx=$(create_mock_kdbx)
    create_mock_keepassxc_cli "${MOCK_MASTER}" "kp_secret_check=testpass123"
    export LOAD_SSH_KEY_DB_PASSWORD="${MOCK_MASTER}"

    run_load_ssh_key -k "${test_key}" -D "${kdbx}" -v

    assert_success
    assert_output_not_contains "testpass123"
    assert_output_not_contains "${MOCK_MASTER}"

    cleanup_mock_keepassxc_cli
}

@test "load-ssh-key.sh: leaves no secret in the sourcing shell" {
    kill_all_ssh_agents
    local test_key=$(create_test_ssh_key "kp_no_leak" "testpass123")
    local kdbx=$(create_mock_kdbx)
    create_mock_keepassxc_cli "${MOCK_MASTER}" "kp_no_leak=testpass123"
    export LOAD_SSH_KEY_DB_PASSWORD="${MOCK_MASTER}"

    local script_path=$(get_script_path)
    run bash -c "
        export HOME='${HOME}'
        source '${script_path}' -k '${test_key}' -D '${kdbx}' >/dev/null 2>&1
        echo \"kp_db_password=[\${kp_db_password:-UNSET}]\"
        echo \"kp_key_passphrase=[\${kp_key_passphrase:-UNSET}]\"
        echo \"askpass_env=[\$(env | grep -c LOAD_SSH_KEY_PASSPHRASE || true)]\"
    "

    assert_output_contains "kp_db_password=\\[UNSET\\]"
    assert_output_contains "kp_key_passphrase=\\[UNSET\\]"
    assert_output_contains "askpass_env=\\[0\\]"
    assert_output_not_contains "testpass123"

    cleanup_mock_keepassxc_cli
}

################################################################################
# Test Config File Resolution
################################################################################

@test "load-ssh-key.sh: reads keepassxc_db from the pub-bin config" {
    kill_all_ssh_agents
    local test_key=$(create_test_ssh_key "kp_from_config" "testpass123")
    local kdbx=$(create_mock_kdbx)
    create_mock_keepassxc_cli "${MOCK_MASTER}" "kp_from_config=testpass123"
    export LOAD_SSH_KEY_DB_PASSWORD="${MOCK_MASTER}"

    # HOME is the test tmpdir, so this is the config the script will read
    mkdir -p "${HOME}/.config/pub-bin"
    cat<<EOF > "${HOME}/.config/pub-bin/config"
screenshot_dir="/tmp/unused"
keepassxc_db="${kdbx}"
EOF

    run_load_ssh_key -k "${test_key}" -v

    assert_success
    assert_output_contains "KEEPASS_DB=\\[${kdbx}\\]"
    assert_output_contains "Using KeePassXC passphrase for: kp_from_config"

    rm -f "${HOME}/.config/pub-bin/config"
    cleanup_mock_keepassxc_cli
}
