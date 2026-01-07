#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(dirname $0)

################################################################################
# CLI Parameters
################################################################################
QUIET=false
VERBOSE=false
FORCE=false

################################################################################
# show command usage
################################################################################
function usage {
    #default message to blank if not passed
    message=${1:-}
    if [ ! -z "${message}" ] ; then
	echo "Message: ${message}" >&2
    fi
    cat<<EOF
Usage: ${script_name} [-hqvf]

Create or update ~/.secure/trufflehog-aws-keys.sh with AWS credentials for use with
trufflehog-rotate-aws-key.py credential loader.

This script securely prompts for:
  - New AWS Access Key ID
  - New AWS Secret Access Key
  - Old AWS Secret Access Key (for paired secret rotation, optional)

If the credentials file already exists, existing values are read and used as defaults.
Press Enter to keep existing values, or enter new values to update.

Creates the credentials file with proper permissions (600).

Options
  -h               : Display this help message.
  -q               : Quiet mode. Output as little as possible.
  -v               : Verbose output.
  -f               : Force mode. Overwrite existing file without reading current values.

Example:
$ ${script_name}
EOF
}

################################################################################
# get command line options
################################################################################
while getopts ":hqvf" opt; do
    case ${opt} in
	q )
            QUIET=true
            ;;
	v )
            VERBOSE=true
            ;;
	f )
            FORCE=true
            ;;
	h )
            usage
            exit 0
            ;;
	\? )
            usage "Invalid Option: -$OPTARG"
            exit 1
            ;;
	: )
            usage "Option -$OPTARG requires an argument"
            exit 1
            ;;
    esac
done
shift $((OPTIND -1))

################################################################################
# functions
################################################################################

function read-existing-credentials {
    local credentials_file="${1}"
    local existing_key=""
    local existing_secret=""
    local existing_old_secret=""
    
    if [ -f "${credentials_file}" ] ; then
	# Read existing values from file
	while IFS= read -r line ; do
	    # Match: export TRUFFLEHOG_NEW_AWS_KEY="value" or export TRUFFLEHOG_NEW_AWS_KEY='value' or export TRUFFLEHOG_NEW_AWS_KEY=value
	    if [[ "${line}" =~ ^export[[:space:]]+TRUFFLEHOG_NEW_AWS_KEY=(.*)$ ]] ; then
		# Extract value and strip quotes
		existing_key="${BASH_REMATCH[1]}"
		existing_key="${existing_key#\"}"  # Remove leading double quote
		existing_key="${existing_key%\"}"   # Remove trailing double quote
		existing_key="${existing_key#\'}"   # Remove leading single quote
		existing_key="${existing_key%\'}"   # Remove trailing single quote
	    elif [[ "${line}" =~ ^export[[:space:]]+TRUFFLEHOG_NEW_AWS_SECRET_KEY=(.*)$ ]] ; then
		existing_secret="${BASH_REMATCH[1]}"
		existing_secret="${existing_secret#\"}"
		existing_secret="${existing_secret%\"}"
		existing_secret="${existing_secret#\'}"
		existing_secret="${existing_secret%\'}"
	    elif [[ "${line}" =~ ^export[[:space:]]+TRUFFLEHOG_OLD_AWS_SECRET_KEY=(.*)$ ]] ; then
		existing_old_secret="${BASH_REMATCH[1]}"
		existing_old_secret="${existing_old_secret#\"}"
		existing_old_secret="${existing_old_secret%\"}"
		existing_old_secret="${existing_old_secret#\'}"
		existing_old_secret="${existing_old_secret%\'}"
	    fi
	done < "${credentials_file}"
    fi
    
    echo "${existing_key}|${existing_secret}|${existing_old_secret}"
}

function create-credentials-file {
    local credentials_file="${HOME}/.secure/trufflehog-aws-keys.sh"
    local secure_dir="${HOME}/.secure"
    
    # Create .secure directory if it doesn't exist
    if [ ! -d "${secure_dir}" ] ; then
	${QUIET} || echo "Creating secure directory: ${secure_dir}" >&2
	mkdir -p "${secure_dir}"
	chmod 700 "${secure_dir}"
    fi
    
    # Read existing credentials if file exists
    local existing_creds=""
    local existing_key=""
    local existing_secret=""
    local existing_old_secret=""
    
    if [ -f "${credentials_file}" ] ; then
	if [ "${FORCE}" != "true" ] ; then
	    ${QUIET} || echo "Reading existing credentials from: ${credentials_file}" >&2
	    existing_creds=$(read-existing-credentials "${credentials_file}")
	    IFS='|' read -r existing_key existing_secret existing_old_secret <<< "${existing_creds}"
	    
	    if [ -n "${existing_key}" ] || [ -n "${existing_secret}" ] || [ -n "${existing_old_secret}" ] ; then
		${QUIET} || echo "Existing credentials found. Press Enter to keep existing value, or enter new value." >&2
		${QUIET} || echo "" >&2
	    fi
	else
	    ${QUIET} || echo "Force mode: Will overwrite existing file without reading current values." >&2
	fi
    fi
    
    # Prompt for AWS Access Key ID
    if [ -n "${existing_key}" ] ; then
	${QUIET} || echo "Enter new AWS Access Key ID (press Enter to keep existing, input will be hidden):" >&2
    else
	${QUIET} || echo "Enter new AWS Access Key ID (input will be hidden):" >&2
    fi
    read -s aws_access_key_id
    echo "" >&2  # New line after hidden input
    
    # Use existing value if user just pressed Enter
    if [ -z "${aws_access_key_id}" ] && [ -n "${existing_key}" ] ; then
	aws_access_key_id="${existing_key}"
	${QUIET} || echo "Using existing AWS Access Key ID" >&2
    fi
    
    if [ -z "${aws_access_key_id}" ] ; then
	echo "ERROR: AWS Access Key ID cannot be empty" >&2
	exit 1
    fi
    
    # Validate AWS Access Key ID format (should start with AKIA and be 20 chars)
    if [[ ! "${aws_access_key_id}" =~ ^AKIA[0-9A-Z]{16}$ ]] ; then
	echo "WARNING: AWS Access Key ID format may be invalid (should start with AKIA and be 20 characters)" >&2
	if [ "${QUIET}" = "true" ] ; then
	    echo "ERROR: Validation failed in quiet mode. Aborting." >&2
	    exit 1
	fi
	read -p "Continue anyway? (y/N): " confirm
	if [ "${confirm}" != "y" ] && [ "${confirm}" != "Y" ] ; then
	    echo "Aborted." >&2
	    exit 1
	fi
    fi
    
    # Prompt for AWS Secret Access Key
    if [ -n "${existing_secret}" ] ; then
	${QUIET} || echo "Enter new AWS Secret Access Key (press Enter to keep existing, input will be hidden):" >&2
    else
	${QUIET} || echo "Enter new AWS Secret Access Key (input will be hidden):" >&2
    fi
    read -s aws_secret_key
    echo "" >&2  # New line after hidden input
    
    # Use existing value if user just pressed Enter
    if [ -z "${aws_secret_key}" ] && [ -n "${existing_secret}" ] ; then
	aws_secret_key="${existing_secret}"
	${QUIET} || echo "Using existing AWS Secret Access Key" >&2
    fi
    
    if [ -z "${aws_secret_key}" ] ; then
	echo "ERROR: AWS Secret Access Key cannot be empty" >&2
	exit 1
    fi
    
    # Validate AWS Secret Access Key format (should be 40 characters)
    if [ ${#aws_secret_key} -ne 40 ] ; then
	echo "WARNING: AWS Secret Access Key format may be invalid (should be 40 characters, got ${#aws_secret_key})" >&2
	if [ "${QUIET}" = "true" ] ; then
	    echo "ERROR: Validation failed in quiet mode. Aborting." >&2
	    exit 1
	fi
	read -p "Continue anyway? (y/N): " confirm
	if [ "${confirm}" != "y" ] && [ "${confirm}" != "Y" ] ; then
	    echo "Aborted." >&2
	    exit 1
	fi
    fi
    
    # Prompt for old AWS Secret Access Key (required for paired secret rotation)
    if [ -n "${existing_old_secret}" ] ; then
	${QUIET} || echo "Enter old paired secret (press Enter to keep existing, input will be hidden):" >&2
    else
	${QUIET} || echo "Enter old paired secret (input will be hidden, optional):" >&2
    fi
    read -s aws_old_secret_key
    echo "" >&2  # New line after hidden input
    
    # Use existing value if user just pressed Enter
    if [ -z "${aws_old_secret_key}" ] && [ -n "${existing_old_secret}" ] ; then
	aws_old_secret_key="${existing_old_secret}"
	${QUIET} || echo "Using existing old AWS Secret Access Key" >&2
    fi
    
    # Old secret key is optional (can be empty if not doing paired secret rotation)
    # But validate format if provided
    if [ -n "${aws_old_secret_key}" ] ; then
	if [ ${#aws_old_secret_key} -ne 40 ] ; then
	    echo "WARNING: Old AWS Secret Access Key format may be invalid (should be 40 characters, got ${#aws_old_secret_key})" >&2
	    if [ "${QUIET}" = "true" ] ; then
		echo "ERROR: Validation failed in quiet mode. Aborting." >&2
		exit 1
	    fi
	    read -p "Continue anyway? (y/N): " confirm
	    if [ "${confirm}" != "y" ] && [ "${confirm}" != "Y" ] ; then
		echo "Aborted." >&2
		exit 1
	    fi
	fi
    fi
    
    # Create credentials file
    ${QUIET} || echo "Creating credentials file: ${credentials_file}" >&2
    
    # Build credentials file content
    cat > "${credentials_file}" <<EOF
export TRUFFLEHOG_NEW_AWS_KEY="${aws_access_key_id}"
export TRUFFLEHOG_NEW_AWS_SECRET_KEY="${aws_secret_key}"
EOF
    
    # Add old secret key if provided
    if [ -n "${aws_old_secret_key}" ] ; then
	cat >> "${credentials_file}" <<EOF
export TRUFFLEHOG_OLD_AWS_SECRET_KEY="${aws_old_secret_key}"
EOF
    fi
    
    # Set restrictive permissions (read/write for owner only)
    chmod 600 "${credentials_file}"
    
    ${QUIET} || echo "Credentials file created successfully: ${credentials_file}" >&2
    ${QUIET} || echo "File permissions set to 600 (read/write for owner only)" >&2
    
    ${VERBOSE} && cat<<EOF>&2
================================================================================
Credentials file created:
  File: ${credentials_file}
  Permissions: $(stat -f "%Sp" "${credentials_file}" 2>/dev/null || stat -c "%a" "${credentials_file}" 2>/dev/null)
  Size: $(stat -f "%z" "${credentials_file}" 2>/dev/null || stat -c "%s" "${credentials_file}" 2>/dev/null) bytes
================================================================================
EOF
}

################################################################################
# main script logic
################################################################################

${VERBOSE} && cat<<EOF>&2
================================================================================
Configuration
================================================================================
QUIET=[${QUIET}]
VERBOSE=[${VERBOSE}]
FORCE=[${FORCE}]
================================================================================
EOF

create-credentials-file

exit 0
