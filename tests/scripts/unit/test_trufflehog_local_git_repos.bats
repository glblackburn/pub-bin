#!/usr/bin/env bats
# Test file for trufflehog-local-git-repos.sh

load '../test_helper.bash'

@test "trufflehog-local-git-repos.sh: script exists and is executable" {
    local script_path=$(get_script_path "trufflehog/trufflehog-local-git-repos.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "trufflehog-local-git-repos.sh: has valid bash syntax" {
    skip_if_command_missing "bash"
    local script_path=$(get_script_path "trufflehog/trufflehog-local-git-repos.sh")
    run bash -n "${script_path}"
    assert_success
}

@test "trufflehog-local-git-repos.sh: help option works" {
    run_script "trufflehog/trufflehog-local-git-repos.sh" -h
    assert_success
    assert_output_contains "Usage:"
    assert_output_contains "trufflehog"
}

@test "trufflehog-local-git-repos.sh: requires directory argument" {
    run_script "trufflehog/trufflehog-local-git-repos.sh"
    assert_failure
}

@test "trufflehog-local-git-repos.sh: requires find command" {
    skip_if_command_missing "find"
}

@test "trufflehog-local-git-repos.sh: requires trufflehog command" {
    skip_if_command_missing "trufflehog"
}

@test "trufflehog-local-git-repos.sh: handles non-existent directory" {
    run_script "trufflehog/trufflehog-local-git-repos.sh" -d "/nonexistent/dir"
    assert_failure
}
