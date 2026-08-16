#!/usr/bin/env bash
# Mock keepassxc-cli for load-ssh-key.sh tests.
#
# Mimics the only two invocations load-ssh-key.sh makes:
#   keepassxc-cli db-info -q <db>                      (master password check)
#   keepassxc-cli show -q -s -a Password <db> <entry>   (entry lookup)
#
# Like the real CLI with stdin piped, the database password is read from stdin.
# Like the real CLI with -q, failures are silent with exit code 1.
#
# State arrives through the environment:
#   MOCK_KEEPASS_MASTER  - password that unlocks the fake database
#   MOCK_KEEPASS_ENTRIES - file of "entry_path=passphrase" lines
#   MOCK_KEEPASS_LOG     - optional file; every invocation appends its argv

set -u

command_name="${1:-}"
shift || true

attribute=""
positional=()
while [ $# -gt 0 ] ; do
    case "$1" in
        -a|--attributes)
            shift
            attribute="${1:-}"
            ;;
        -q|--quiet|-s|--show-protected)
            :
            ;;
        *)
            positional+=("$1")
            ;;
    esac
    shift
done

if [ -n "${MOCK_KEEPASS_LOG:-}" ] ; then
    echo "${command_name} ${positional[@]+${positional[@]}}" >> "${MOCK_KEEPASS_LOG}"
fi

# The real CLI reads the database password from stdin when stdin is not a tty
IFS= read -r given_password || given_password=""
[ "${given_password}" = "${MOCK_KEEPASS_MASTER:-}" ] || exit 1

case "${command_name}" in
    db-info)
        exit 0
        ;;
    show)
        :
        ;;
    *)
        exit 1
        ;;
esac

# positional[0] is the database path, positional[1] is the entry
entry="${positional[1]:-}"
[ -n "${entry}" ] || exit 1
[ "${attribute}" = "Password" ] || exit 1
[ -f "${MOCK_KEEPASS_ENTRIES:-}" ] || exit 1

while IFS= read -r line ; do
    case "${line}" in
        "${entry}="*)
            printf '%s\n' "${line#*=}"
            exit 0
            ;;
    esac
done < "${MOCK_KEEPASS_ENTRIES}"

exit 1
