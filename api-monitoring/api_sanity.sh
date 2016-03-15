#!/bin/sh
unset http_proxy
unset https_proxy
sanityType=$1
folder="/home/obj_team/monitoring/api-sanity/"

create_log_file () {
    logfile_name=$1
    rm /home/obj_team/monitoring/api-sanity/$logfile_name.*
    current_time=$(date "+%Y.%m.%d-%H.%M.%S")
    #echo $current_time
    logfile=$folder$logfile_name.$current_time.txt
    echo $logfile
}

get_sanity_result () {
    #check status of api sanity check
    result=`grep ": Sanity Test Failed" $1`

    if [ -n "$result" ]; then
        status=2
    elif [ -z "$result" ]; then
        status=0
    fi
    echo $status
}

get_logpath() {
    logpath=`python /home/obj_team/monitoring/api-sanity/upload_log_files.py $logfile_iam 2>&1 >> /tmp/sigout.txt`
    echo $logpath
    rm /tmp/sigout.txt
}

logfile_iam=$(create_log_file "api_sanity_logs_iam")
echo "THIS IS THE LOG FILE: $logfile_iam"
`python /home/obj_team/monitoring/api-sanity/sanity_tests_monitoring.py -a '2bf9f42cc7fa47fdae06f14dddd7e4ac' -s 'eda0b04c73c248fda507569ead1d7176' > $logfile_iam` 
status_iam=$(get_sanity_result "$logfile_iam")
if [ "$sanityType" -eq "1" ]; then
    if [ "$status_iam" == 2 ]; then
        echo " test running for iam failed with priprity 1"
        logfile_rgw=$(create_log_file "api_sanity_logs_rgw")
        `python /home/obj_team/monitoring/api-sanity/sanity_tests_monitoring.py -a '0e041b091ead45c6b183bcb79626c0fc' -s 'bcec52ffaa5a48648601389bceac1b18' > $logfile_rgw`
        status_rgw=$(get_sanity_result "$logfile_rgw")
        statustxt="CRITICAL"
        status_rgw=0
        if [ "$status_rgw" == 2 ]; then
            echo "test running for both failec with priority 1"
            status_message="Both verification (with iam keys and rgw keys failed)."
            echo "Api Sanity status: $status_message" | mail -s "DSS api sanity Test $statustxt (10 min test)" --attach=$logfile_rgw --attach=$logfile_rgw -a "From: dssSanity@ril.com" harshal.gupta@ril.com,shivanshu.goswami@ril.com,praveen.p.prakash@ ril.com,gaurav.bafna@ril.com,rajat.garg@ril.com,abhishek.s.dixit@ril.com,rahul.aggarwal@ril.com
        else
            echo "test running for only iam failed with priority 1"
            logpath_iam=$(get_logpath)
            echo "this is the log path: $logpath_iam"
            status_message="Sanity with iam keys failed but with rgw keys passed."
            status_string="DSS API test completed with response $status_message. Logs for iam keys can be viewed at: $logpath_iam"
            echo "Api Sanity status: $status_string" | mail -s "DSS api sanity Test $statustxt (10 min test)" -a "From: dssSanity@ril.com" harshal.gupta@ril.com,shivanshu.goswami@ril.com,praveen.p.prakash@ ril.com,gaurav.bafna@ril.com,rajat.garg@ril.com,abhishek.s.dixit@ril.com,rahul.aggarwal@ril.com
        fi
    fi
else
    if [ "$status_iam" == 2 ]; then
        echo " test running for iam failed with priprity 2"
        logfile_rgw=$(create_log_file "api_sanity_logs_rgw")
        `python /home/obj_team/monitoring/api-sanity/sanity_tests_monitoring.py -a '0e041b091ead45c6b183bcb79626c0fc' -s 'bcec52ffaa5a48648601389bceac1b18' > $logfile_rgw`
        status_rgw=$(get_sanity_result "$logfile_rgw")
        statustxt="CRITICAL"
        if [ "$status_rgw" == 2 ]; then
            echo "test running for both failec with priority 2"
            status_message="Both verification (with iam keys and rgw keys failed)."
            echo "Api Sanity status: $status_message" | mail -s "DSS api sanity Test $statustxt (30 min test)" --attach=$logfile_rgw --attach=$logfile_rgw -a "From: dssSanity@ril.com" harshal.gupta@ril.com,shivanshu.goswami@ril.com,praveen.p.prakash@ ril.com,gaurav.bafna@ril.com,rajat.garg@ril.com,abhishek.s.dixit@ril.com,rahul.aggarwal@ril.com
        else
            echo "test running for only iam failed with priority 2"
            logpath_iam=$(get_logpath)
            status_message="Sanity with iam keys failed but with rgw keys passed."
            status_string="DSS API test completed with response $status_message. Logs for iam keys can be viewed at: $logpath_iam"
            echo "Api Sanity status: $status_string" | mail -s "DSS api sanity Test $statustxt (30 min test)" -a "From: dssSanity@ril.com" harshal.gupta@ril.com,shivanshu.goswami@ril.com,praveen.p.prakash@ ril.com,gaurav.bafna@ril.com,rajat.garg@ril.com,abhishek.s.dixit@ril.com,rahul.aggarwal@ril.com
        fi
    else
            echo "test runing for both passed with priority 2"
            statustxt="OK"
            status_message="API Sanity Passed."
            logpath_iam=$(get_logpath)
            status_string="DSS API test completed with response $status_message. Logs for iam keys can be viewed at: $logpath_iam"
            echo "Api Sanity status: $status_string" | mail -s "DSS api sanity Test $statustxt (30 min test)" -a "From: dssSanity@ril.com" harshal.gupta@ril.com,shivanshu.goswami@ril.com,praveen.p.prakash@ril.com,gaurav.bafna@ril.com,rajat.garg@ril.com,abhishek.s.dixit@ril.com,rahul.aggarwal@ril.com
    fi
fi

export http_proxy="http://10.140.218.59:3128"
export https_proxy="http://10.140.218.59:3128"
