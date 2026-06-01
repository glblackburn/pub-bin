#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(dirname $0)

################################################################################
# CLI Parameters
################################################################################
JSON=false

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
Usage: ${script_name} [-h] [-j|--json]

Discover this host's public IPv4 and IPv6 addresses (via DNS to Cloudflare
and Google) and look up geo / ISP / ASN information for the IPv4 via
ip-api-json.sh.  All output is mirrored to ${log_dir}/.

Options
  -h, --help       : Display this help message.
  -j, --json       : Emit a single JSON object instead of the human-readable
                     report.  The same log file is still written.

Output
  Default mode: human-readable lines for IPv4, IPv6, and a one-line
                Location/ISP summary derived from the geo lookup.
  JSON mode:    { "ts": ..., "ipv4": ..., "ipv6": ..., "geo": { ... } }

Log file
  ${log_dir}/${script_name%.*}_<timestamp>.log

Example:
\$ ${script_name}
\$ ${script_name} --json | jq .geo.country
EOF
}

################################################################################
# get command line options
################################################################################
# Translate the long --json / --help forms to their short equivalents so we
# can keep using getopts (which does not natively understand long options).
if [ $# -gt 0 ] ; then
    _args=()
    for _arg in "$@" ; do
        case "${_arg}" in
            --json) _args+=("-j") ;;
            --help) _args+=("-h") ;;
            *)      _args+=("${_arg}") ;;
        esac
    done
    set -- "${_args[@]}"
    unset _arg _args
fi

while getopts ":hj" opt; do
    case ${opt} in
	h )
            usage
            exit 0
            ;;
	j )
            JSON=true
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

if [ "${JSON}" = "true" ] ; then
    # Compose a single JSON object.  Use jq -n so missing fields stay null.
    jq -n \
        --arg ts "${ts}" \
        --arg ipv4 "${ipv4}" \
        --arg ipv6 "${ipv6}" \
        --argjson geo "${geo}" \
        '{ts: $ts, ipv4: $ipv4, ipv6: $ipv6, geo: $geo}' \
        | tee ${log_file}
else
    # Human-readable mode: extract a short location summary from the geo
    # payload (best-effort; missing fields become empty strings).
    location=$(echo "${geo}" | jq -r '
        [.city, .regionName, .country, .isp]
        | map(select(. != null and . != ""))
        | join(", ")
    ' 2>/dev/null || true)
    {
        date
        echo "IPv4: ${ipv4}"
        echo "IPv6: ${ipv6}"
        if [ -n "${location}" ] ; then
            echo "Location: ${location}"
        fi
        cat<<EOF
log_file=[${log_file}]
EOF
    } | tee ${log_file}
fi
