#!/usr/bin/env bats
# Test file for clean-downloads.sh

load '../test_helper.bash'

setup_downloads() {
    local src=$1
    mkdir -p "${src}/old/2026-01-01_000000" "${src}/some dir"
    touch "${src}/file one.pdf" "${src}/file2.zip" "${src}/.DS_Store" "${src}/some dir/inner.txt"
}

@test "clean-downloads.sh: script exists and is executable" {
    local script_path=$(get_script_path "clean-downloads.sh")
    [ -f "${script_path}" ]
    [ -x "${script_path}" ]
}

@test "clean-downloads.sh: has valid bash syntax" {
    local script_path=$(get_script_path "clean-downloads.sh")
    run bash -n "${script_path}"
    assert_success
}

@test "clean-downloads.sh: help option works" {
    run_script "clean-downloads.sh" -h
    assert_success
    assert_output_contains "Usage:"
}

@test "clean-downloads.sh: fails on missing source dir" {
    run_script "clean-downloads.sh" -s "${TEST_TMPDIR}/does-not-exist"
    assert_failure
}

@test "clean-downloads.sh: dry run moves nothing" {
    local src="${BATS_TEST_TMPDIR}/Downloads"
    setup_downloads "${src}"
    run_script "clean-downloads.sh" -n -s "${src}"
    assert_success
    assert_output_contains "DRY RUN"
    [ -f "${src}/file one.pdf" ]
    [ -d "${src}/some dir" ]
    [ "$(ls "${src}/old")" = "2026-01-01_000000" ]
}

@test "clean-downloads.sh: moves everything except old/ and dot files" {
    local src="${BATS_TEST_TMPDIR}/Downloads"
    setup_downloads "${src}"
    run_script "clean-downloads.sh" -s "${src}"
    assert_success
    local archive=$(ls -d "${src}"/old/2*_* | grep -v 2026-01-01_000000)
    [ -f "${archive}/file one.pdf" ]
    [ -f "${archive}/file2.zip" ]
    [ -f "${archive}/some dir/inner.txt" ]
    [ -f "${src}/.DS_Store" ]
    [ -d "${src}/old/2026-01-01_000000" ]
    [ "$(ls "${src}")" = "old" ]
}

@test "clean-downloads.sh: empty source dir is a no-op" {
    local src="${BATS_TEST_TMPDIR}/Downloads"
    mkdir -p "${src}"
    run_script "clean-downloads.sh" -s "${src}"
    assert_success
    assert_output_contains "Nothing to move"
    [ ! -e "${src}/old" ]
}
