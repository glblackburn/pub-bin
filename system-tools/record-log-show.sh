
log_dir=${HOME}/log
log=${log_dir}/log-show_`date +%Y-%m-%d_%H%M%S`.log

today=`date +%Y-%m-%d`
log show --start ${today} --style syslog --predicate 'process == "loginwindow"' --debug --info |
#    grep 2025-01-16 |
    tee ${log}

cat<<EOF
================================================================================
log=[${log}]
================================================================================
EOF
cat  ${log} | grep "LWScreenLock startUnlock" | grep "inform UA unlocked"

cat<<EOF
================================================================================
log=[${log}]
================================================================================
EOF
