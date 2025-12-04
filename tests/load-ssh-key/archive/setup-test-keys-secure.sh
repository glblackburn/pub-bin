#!/usr/bin/env bash
# Setup helper for creating test keys config in secure directory
# Follows the pattern from create-set-api-key.sh

set -euET -o pipefail

script_name=$(basename "${0}")
script_dir=$(dirname "${0}")

################################################################################
# Configuration
################################################################################
secure_dir=${HOME}/.secure
set_test_keys=${secure_dir}/load-ssh-key-test-keys.sh

################################################################################
# show command usage
################################################################################
function usage {
    local message=${1:-}
    if [ ! -z "${message}" ] ; then
	echo "Message: ${message}"
    fi
cat<<EOF
Usage: ${script_name} [-h]
Create and store SSH test key configuration securely.

This script will prompt for:
  - Test key without passphrase (for basic tests)
  - Test key with passphrase (for passphrase tests)

The configuration will be stored in: ${set_test_keys}

Options
  -h               : Display this help message.
EOF
}

################################################################################
# get command line options
################################################################################
while getopts ":h" opt; do
    case ${opt} in
	h )
            usage
            exit 0
            ;;
	\? )
            usage "Invalid Option: -$OPTARG"
            exit 1
            ;;
    esac
done
shift $((OPTIND -1))

################################################################################
# main script logic
################################################################################

cat<<EOF
================================================================================
set_test_keys=[${set_test_keys}]
================================================================================
EOF

# Load existing values if file exists
EXISTING_KEY_NO_PASS=""
EXISTING_KEY_WITH_PASS=""
EXISTING_KEY_2=""
EXISTING_KEY_3=""

if [ -e "${set_test_keys}" ] ; then
    cat<<EOF
WARNING: ${set_test_keys} already exists.
Do you want to overwrite it? (y/N)
EOF
    read response
    if [ "${response}" != "y" ] && [ "${response}" != "Y" ] ; then
        cat<<EOF
Exiting without changes. To manually delete the file, run:
  rm ${set_test_keys}
EOF
        exit 0
    fi
    cat<<EOF
Overwriting existing configuration file.
Loading existing values to use as defaults...
EOF
    # Temporarily disable set -u to safely source the file
    set +u
    . ${set_test_keys} 2>/dev/null || true
    EXISTING_KEY_NO_PASS="${TEST_KEY_NO_PASSPHRASE:-}"
    EXISTING_KEY_WITH_PASS="${TEST_KEY_WITH_PASSPHRASE:-}"
    EXISTING_KEY_2="${TEST_KEY_2:-}"
    EXISTING_KEY_3="${TEST_KEY_3:-}"
    set -u
fi

cat<<EOF
Go get your SSH key names from ${HOME}/.ssh/
Press Enter to continue.
EOF
read continue

if [ -z "${EXISTING_KEY_NO_PASS}" ] ; then
    cat<<EOF
Enter Test Key WITHOUT passphrase (for basic tests):
EOF
else
    cat<<EOF
Enter Test Key WITHOUT passphrase (current: ${EXISTING_KEY_NO_PASS}):
EOF
fi
read TEST_KEY_NO_PASSPHRASE
if [ -z "${TEST_KEY_NO_PASSPHRASE}" ] ; then
    TEST_KEY_NO_PASSPHRASE="${EXISTING_KEY_NO_PASS}"
fi

if [ -z "${EXISTING_KEY_WITH_PASS}" ] ; then
    cat<<EOF
Enter Test Key WITH passphrase (for passphrase tests):
EOF
else
    cat<<EOF
Enter Test Key WITH passphrase (current: ${EXISTING_KEY_WITH_PASS}):
EOF
fi
read TEST_KEY_WITH_PASSPHRASE
if [ -z "${TEST_KEY_WITH_PASSPHRASE}" ] ; then
    TEST_KEY_WITH_PASSPHRASE="${EXISTING_KEY_WITH_PASS}"
fi

if [ -z "${TEST_KEY_NO_PASSPHRASE}" ] ; then
    cat<<EOF
ERROR: Test key without passphrase is required.
EOF
    exit 1
fi

if [ -z "${TEST_KEY_WITH_PASSPHRASE}" ] ; then
    cat<<EOF
ERROR: Test key with passphrase is required.
EOF
    exit 1
fi

cat<<EOF
================================================================================
check / create secure_dir
secure_dir=[${secure_dir}]
================================================================================
EOF
mkdir -p ${secure_dir}
chmod 700 ${secure_dir}

cat<<EOF
================================================================================
create set_test_keys script
set_test_keys=[${set_test_keys}]
================================================================================
EOF

# Write to temporary file first, then move to final location
# This ensures we don't lose the existing file if something goes wrong
temp_file=$(mktemp "${secure_dir}/load-ssh-key-test-keys.sh.XXXXXX")

cat<<EOF>${temp_file}
# SSH Key Configuration for Tests
# This file is in ~/.secure/ with restricted permissions

export TEST_KEY_NO_PASSPHRASE="${TEST_KEY_NO_PASSPHRASE}"
export TEST_KEY_WITH_PASSPHRASE="${TEST_KEY_WITH_PASSPHRASE}"
export TEST_KEY_2="${TEST_KEY_2:-}"
export TEST_KEY_3="${TEST_KEY_3:-}"
EOF
chmod 400 ${temp_file}

# Move temp file to final location (mv will overwrite even read-only files)
mv -f ${temp_file} ${set_test_keys}

cat<<EOF
================================================================================
Script created
set_test_keys=[${set_test_keys}]
================================================================================
EOF
ls -lad ${secure_dir}
ls -la ${set_test_keys}
