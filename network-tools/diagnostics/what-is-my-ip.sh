#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(dirname $0)

################################################################################
# CLI Parameters
################################################################################
HUMAN=false

################################################################################
# default values
################################################################################
log_dir=${HOME}/log/ip_log
ts=`date +%Y-%m-%d_%H%M%S`
log_file=${log_dir}/${script_name%.*}_${ts}.log

################################################################################
# show command usage
################################################################################
function usage {
    message=${1:-}
    if [ ! -z "${message}" ] ; then
	echo "Message: ${message}"
    fi
    cat<<EOF
Usage: ${script_name} [-h] [-H|--human]

Discover this host's public IPv4 and IPv6 addresses (via DNS to Cloudflare
and Google) and look up geo / ISP / ASN information for the IPv4 via
ip-api-json.sh.  The log file (always JSON) is written to ${log_dir}/.

Options
  -h, --help       : Display this help message.
  -H, --human      : Emit a human-readable report on stdout instead of the
                     default JSON object.  The log file is JSON regardless.

Output
  Default mode: single JSON object { "ts": ..., "ipv4": ..., "ipv6": ...,
                                     "geo": { ... } }
  Human mode:   human-readable lines for IPv4, IPv6, and a one-line
                Location/ISP summary derived from the geo lookup.

Log file
  ${log_dir}/${script_name%.*}_<timestamp>.log  (JSON, always)

Example:
\$ ${script_name} | jq .geo.country
\$ ${script_name} --human
EOF
}

################################################################################
# get command line options
################################################################################
# Translate the long --human / --help forms to their short equivalents so we
# can keep using getopts (which does not natively understand long options).
if [ $# -gt 0 ] ; then
    _args=()
    for _arg in "$@" ; do
        case "${_arg}" in
            --human) _args+=("-H") ;;
            --help)  _args+=("-h") ;;
            *)       _args+=("${_arg}") ;;
        esac
    done
    set -- "${_args[@]}"
    unset _arg _args
fi

while getopts ":hH" opt; do
    case ${opt} in
	h )
            usage
            exit 0
            ;;
	H )
            HUMAN=true
            ;;
	\? )
            usage "Invalid Option: -$OPTARG"
            exit 1
            ;;
    esac
done
shift $((OPTIND -1))

################################################################################
# functions
################################################################################
function lookup_ipv4 {
    dig +short txt ch whoami.cloudflare @1.0.0.1 2>/dev/null | tr -d '"' || true
}

function lookup_ipv6 {
    dig -6 TXT +short o-o.myaddr.l.google.com @ns1.google.com 2>/dev/null \
        | tr -d '"' || true
}

function lookup_geo {
    # Print the raw ip-api JSON for the given IPv4, or {} on any failure.
    local ip=${1:-}
    if [ -z "${ip}" ] ; then
        echo "{}"
        return 0
    fi
    local body
    body=$(ip-api-json.sh "${ip}" 2>/dev/null) || body=""
    if [ -z "${body}" ] ; then
        echo "{}"
    else
        echo "${body}"
    fi
}

################################################################################
# main script logic
################################################################################
mkdir -p ${log_dir}

ipv4=$(lookup_ipv4)
ipv6=$(lookup_ipv6)
geo=$(lookup_geo "${ipv4}")

# Always compose and persist the JSON payload (single source of truth).
jq -n \
    --arg ts "${ts}" \
    --arg ipv4 "${ipv4}" \
    --arg ipv6 "${ipv6}" \
    --argjson geo "${geo}" \
    '{ts: $ts, ipv4: $ipv4, ipv6: $ipv6, geo: $geo}' \
    > ${log_file}

if [ "${HUMAN}" = "true" ] ; then
    # Human-readable mode: extract a short location summary from the geo
    # payload (best-effort; missing fields become empty strings).
    location=$(echo "${geo}" | jq -r '
        [.city, .regionName, .country, .isp]
        | map(select(. != null and . != ""))
        | join(", ")
    ' 2>/dev/null || true)
    date
    echo "IPv4: ${ipv4}"
    echo "IPv6: ${ipv6}"
    if [ -n "${location}" ] ; then
        echo "Location: ${location}"
    fi
    echo "log_file=[${log_file}]"
else
    cat ${log_file}
fi
