#!/bin/bash

# TODO: add cli options and usage function
# TODO: add KEY_TIMEOUT cli option
# TODO: add KEY_LIST cli option
# TODO: add CONFIG cli option

# Load keys from $HOME/.ssh
KEY_LIST=$(find $HOME/.ssh -type f -not -name "*.pub" -not -name "known_hosts*" -not -name "ssh-agent.config")


CONFIG=$HOME/.ssh/ssh-agent.config
# 8 hours
KEY_TIMEOUT=28800
# 30 sec
#KEY_TIMEOUT=30

function startAgent {
    ssh-agent > ${CONFIG}
    echo "loading agent config"
    . ${CONFIG}
}

echo "run this script as . $0 to load into env"
echo "KEY_TIMEOUT=[${KEY_TIMEOUT}]"
echo "CONFIG=[${CONFIG}]"
echo "KEY_LIST=[${KEY_LIST}]"

if [ -e ${CONFIG} ] ; then
    echo "load agent config"
    . ${CONFIG}
else
    echo "start agent for the first time"
    startAgent
fi

#check if agent is running
PS_CHECK=`ps -fe | grep " ${SSH_AGENT_PID} " | grep ssh-agent`
PS_COUNT=`ps -fe | grep " ${SSH_AGENT_PID} " | grep ssh-agent | wc -l`
echo "PS_CHECK=[${PS_CHECK}]"
echo "PS_COUNT=[${PS_COUNT}]"

if [ "1" -ne "${PS_COUNT}" ] ; then
    echo "ssh-agent not running.  starting agent"
    startAgent
else
    echo "ssh-agent is running"
fi

error_count=0;
for key_file in ${KEY_LIST} ; do
    if [ ! -e ${key_file} ] ; then
	echo "### ERROR ### key_file=[${key_file}] does not exists"
	((error_count++))
    else
        KEY_CHECK=`ssh-keygen -l -E sha256 -f ${key_file} | awk '{print $2}'`
        KEY_COUNT=`ssh-add -l | grep "${KEY_CHECK}" | wc -l`
        cat<<EOF
        key_file=[${key_file}]
        KEY_CHECK=[${KEY_CHECK}]
        KEY_COUNT=[${KEY_COUNT}]
EOF
        if [ "1" -ne "${KEY_COUNT}" ] ; then
	    echo "KEY_CHECK not found. listing all loaded keys"
	    ssh-add -l
	    echo "add ssh key to agent"
	    ssh-add -t ${KEY_TIMEOUT} ${key_file}
        fi
    fi
done

echo "only one ssh-agent should be running"
echo "SSH_AGENT_PID=[${SSH_AGENT_PID}]"

echo "show ssh agents"
ps -fe | grep -e ssh-agent -e "PID"

if [ ${error_count} -gt 0 ] ; then
    echo "### ERROR ### key error count=[${error_count}]"
    return 1
fi

date
