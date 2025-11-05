#!/usr/bin/env bash
set -euET -o pipefail

script_name=$(basename $0)
script_dir=$(dirname $0)

################################################################################
# CLI Parameters
################################################################################
QUIET=false
VERBOSE=false
TEST_MODE=false
aws_profile=default-aws-profile
region=default-region

################################################################################
# default values
################################################################################

## pattern for generating date log file in log dir.
#ts=`date +%Y-%m-%d_%H%M%S`
#log_dir=log
#log_file=${log_dir}/${script_name%.*}_${ts}.txt
## uncomment to create log dir
#mkdir -p ${log_dir}
## uncomment to capture log output
#{
#cat<<EOF
#================================================================================
#log_file=[${log_file}]
#================================================================================
#EOF
#} 2>&1 | tee ${log_file}


ts=`date +%Y-%m-%d_%H%M%S`
output=${script_name%.*}_${ts}.txt

file=${script_name%.*}
output=${file}_${ts}.txt

# temp dir
temp_dir=`mktemp -d /tmp/${script_name}.XXXXXX` || exit 1
# temp file
temp_file=`mktemp /tmp/${script_name}.XXXXXX` || exit 1
# https://www.linuxjournal.com/content/bash-trap-command
trap "rm -f ${temp_file} ; rm -rf ${temp_dir}" EXIT

################################################################################
# show command usage
################################################################################
function usage {
    #default message to blank if not passed
    message=${1:-}
    if [ ! -z "${message}" ] ; then
	echo "Message: ${message}"
    fi
    cat<<EOF
Usage: ${script_name} [-hyqv] [-p <aws_profile>]

Show help message for the shell teamplate script.  This shows a good
pattern for implementing cli parameters in a bash script.

Options
  -h               : Display this help message.
  -p <aws_profile> : AWS Profile (Default: ${aws_profile})
  -r <region>      : AWS region (Default: ${region})
  -q               : Quite mode.  output as little as possible. skip ping step
  -t               : Test mode.  Do not create the ticket.
  -v               : Verbose output (may contain sensitive data.  DO NOT use when logging output.)

Example:
$ ${script_name} -p profile_1 -r us-east-1
EOF
}

################################################################################
# get command line options
################################################################################
while getopts ":p:r:hqtv" opt; do
    case ${opt} in
	p )
            aws_profile=$OPTARG
            ;;
	r )
            region=$OPTARG
            ;;
	q )
            QUIET=true
            ;;
	t )
            TEST_MODE=true
            ;;
	v )
            VERBOSE=true
            ;;
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
# functions
################################################################################
function do-a-test-thing {
    cat<<EOF
####################### TEST TEST TEST #########################################
                     This is an example test.
####################### TEST TEST TEST #########################################
EOF
}

################################################################################
# main script logic
################################################################################

cat<<EOF
################################################################################
# CLI Parameters
################################################################################
QUIET=[${QUIET}]
VERBOSE=[${VERBOSE}]
TEST_MODE=[${TEST_MODE}]
aws_profile=[${aws_profile}]
region=[${region}]

################################################################################
# default values
################################################################################
ts=[${ts}]
file=[${file}]
output=[${output}]

EOF

###############################################################################
# colors
################################################################################
red=`tput setaf 1`
green=`tput setaf 2`
yellow=`tput setaf 3`
reset=`tput sgr0`

cat<<EOF
###############################################################################
# colors
################################################################################
${red}red${reset}
${green}green${reset}
${yellow}yellow${reset}
EOF

var1="2"
var2="4"
let var3=var1+var2
let var4=var2-var1
cat<<EOF
================================================================================
How to do math?
${var1} + ${var2} = ${var3}
${var2} - ${var1} = ${var4}
================================================================================
EOF

cat<<EOF
================================================================================
How to line up things?
https://phoenixnap.com/kb/bash-printf
================================================================================
EOF
format='%-20s | %s\n'
column1="column 1"
column2="column 2"
printf "${format}" "${column1}" "${column2}"
column1="a string"
column2="a string"
printf "${format}" "${column1}" "${column2}"
column1="a longer string"
column2="a longer string"
printf "${format}" "${column1}" "${column2}"
cat<<EOF
================================================================================
EOF

cat<<EOF
================================================================================
set terminal window title to hostname
================================================================================
EOF
echo -ne "\033]0;$HOSTNAME\007"

${TEST_MODE} && do-a-test-thing

if [ ${TEST_MODE} == true ] ; then
    echo "Show only when TEST_MODE is true."
fi

if [ ${TEST_MODE} == false ] ; then
    echo "Show only when TEST_MODE is false."
fi

if [ ${QUIET} != true ] ; then
    echo "display if not quiet passes."
fi

if [ ${VERBOSE} == true ] ; then
    echo "display verbose output"
fi

${VERBOSE} && echo "display verbose output another way"

${VERBOSE} && cat<<EOF
display verbose output a third way
EOF

cat<<EOF
Are you sure you want me to do this?
type 'YES' to make it so.
EOF
read response
if [ "YES" == "${response}" ] ; then
    cat<<EOF
Release the hounds........
EOF
else
    cat<<EOF
Okay.  It's your baby.
Stopping and exiting.
EOF
    exit
fi

cat<<EOF
================================================================================
turn echo off to read a secure string
================================================================================
EOF
stty -echo
echo -n "Enter private string: "
read private
stty echo
cat<<EOF
echo back to confirm.  you probably should not do this.
private=[${private}]
EOF

# Calculate epoc date for file and current time
file=/var/log/system.log
epoc_file_date=$(stat -f "%m" ${file})
epoc_date=$(date +"%s")

cat<<EOF
================================================================================
Calculate epoc date for file and current time
================================================================================
file=[${file}]
epoc_file_date=[${epoc_file_date}]
epoc_date     =[${epoc_date}]
$(ls -l ${file})
$(date)
================================================================================
EOF

cat<<EOF
================================================================================
Date string to use in Excel and csv files
================================================================================
$(date +'%Y-%m-%d %H:%M:%S')
================================================================================
EOF

csv_string="one,two,three"
IFS=',' read -r -a array <<< "${csv_string}"
cat<<EOF
================================================================================
demo splitting a string
================================================================================
csv_string="one,two,three"
IFS=',' read -r -a array <<< "\${csv_string}"

csv_string=[${csv_string}]
array[0]=[${array[0]}]
array[1]=[${array[1]}]
array[2]=[${array[2]}]
================================================================================
EOF


cat<<EOF
================================================================================
demo reading input from shell comand into array
================================================================================
EOF
IFS=$'\n'
readarray -t files < <(ls -1 ${script_dir} |
    head -5
)
for file in ${files[@]} ; do
    echo ${file}
done
cat<<EOF
================================================================================
EOF

# # reedarray requires updated version of bash which is not installed by default on mac
# # https://stackoverflow.com/a/74962419
# # brew install bash
# # restart terminal
# IFS=$'\n'
# readarray -t ids < <(cat output/mdr_tickets_2024-08-25_065149.csv |
#     grep '"pending"' |
#     cut -d , -f 2 |
#     head -1
# )
# for id in ${ids[@]} ; do
#     echo ${id}
# done

cat<<EOF
example removing whitespace from wc to use in if check
EOF
cat /var/log/system.log | wc -l | tr -d ' '
line_count=$(cat /var/log/system.log | wc -l | tr -d ' ')
cat<<EOF
line_count=[${line_count}]
EOF
if [ "${line_count}" -gt "0" ] ; then
    echo "line_count > 0"
fi
if [ "${line_count}" -eq "52" ] ; then
    echo "line_count = 52"
fi
if [ "${line_count}" -lt "100" ] ; then
    echo "line_count < 100"
fi
if [ "${line_count}" -gt "1000" ] ; then
    echo "line_count > 1000"
fi

if [ -z "${aws_profile}" ] ; then
    usage "aws_profile is blank"
fi

cat<<EOF
################################################################################
Example of catching and error from a called command or script
################################################################################
EOF
ret=
ls -l ${HOME}/_DNE_* || ret=$?
cat<<EOF
ret=[${ret}]
EOF
if [ ! -z "${ret}" ] ; then
    case ${ret} in
        1 ) echo "WARN: no files" ;;
        * ) msg="ERROR: unknown ls exit status: ${request_dir}"
            ERRORS="${ERRORS}${msg}
"
            cat<<EOF
${msg}
EOF
            ;;
    esac
fi

cat<<EOF
################################################################################
read some json into a string
################################################################################
EOF
read -r -d '' json <<EOF || ret=$? # need to catch exit code from read because returns non-zero status
{
    "AddressLine1": "string",
    "AddressLine2": "string",
    "AddressLine3": "string",
    "City": "string",
    "CompanyName": "string",
    "CountryCode": "string",
    "DistrictOrCounty": "string",
    "FullName": "string",
    "PhoneNumber": "string",
    "PostalCode": "string",
    "StateOrRegion": "string",
    "WebsiteUrl": "string"
}
EOF

echo "after read: ret=[${ret}]"
cat<<EOF
json=[
${json}
]
EOF

echo "send message to stderr"
>&2 echo "this goes to stderr"

cat<<EOF
================================================================================
Ring the bell
================================================================================
EOF
tput bel

#!/bin/bash

N=5 # Replace 5 with your desired upper limit

for ((i = 1; i <= N; i++)); do
    echo "Ring the bell $i"
    tput bel
    sleep 1
done
cat<<EOF
COMPLETED: ${script_name}
EOF
