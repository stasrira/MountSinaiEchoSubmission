#!/bin/bash
set -euo pipefail

#file transfer parameters
source_dir="{!source_dir!}"
target_dir="{!target_dir!}" # "/home/gridsan/groups/ECHO_ISMMS/ISMMS/pub"
transfer_log_file=$source_dir/"transfer_log_"$(date +"%Y%m%d_%H%M%S")".log"

#email parameters
smtp="{!smtp!}" # "smtp.mssm.edu:25"
to_emails="{!to_email!}" # "stasrirak.ms@gmail.com,stas.rirak@mssm.edu"
from_email="{!from_email!}" # "stas.rirak@mssm.edu"
send_email_flag="{!send_email_flag!}" # this will be set to 1 if an email should be sent after completion

echo "$(date +"%Y-%m-%d %H:%M:%S")-->source_dir = "$source_dir 2>&1 | tee -a "$transfer_log_file"
echo "$(date +"%Y-%m-%d %H:%M:%S")-->target_dir = "$target_dir 2>&1 | tee -a "$transfer_log_file"
echo "$(date +"%Y-%m-%d %H:%M:%S")-->transfer_log_file = "$transfer_log_file 2>&1 | tee -a "$transfer_log_file"

cmd="rsync -v -r --exclude='transfer_*.*' -e ssh $source_dir {!ssh_user!}@txe1-login.mit.edu:$target_dir" # srirak

echo "$(date +"%Y-%m-%d %H:%M:%S")-->Transfer command to be executed: '$cmd'" 2>&1 | tee -a "$transfer_log_file"
echo "==============================" | tee -a "$transfer_log_file"

cd $source_dir
# rsync -v -r --exclude='transfer_*.*' -e ssh $source_di srirak@txe1-login.mit.edu:$target_dir 2>&1 | tee -a "$transfer_log_file"
if echo "${cmd}" |bash 2>&1 | tee -a "$transfer_log_file"; then
	process_status=0
	echo "==============================" | tee -a "$transfer_log_file"
	echo "$(date +"%Y-%m-%d %H:%M:%S")-->SUCCESS: Transfer completed successfully.'" 2>&1 | tee -a "$transfer_log_file"
else
	process_status=1
	echo "==============================" | tee -a "$transfer_log_file"
	echo "$(date +"%Y-%m-%d %H:%M:%S")-->ERROR: Some errors were reported during transfer. Check earlier output in this file.'" 2>&1 | tee -a "$transfer_log_file"
fi

#send email about completion of the process
#prepare an email parameters to send status of the process
attch_req_log="--attach-type text/plain --attach $transfer_log_file"

if [ "$process_status" == "1" ]; then
	#errors happened
	email_body="Transfer of the folder '$source_dir' completed with ERRORS. See attached log file for details."
	subject="Subject: ERRORS reported during transfer of files for directory: "$(basename $source_dir)
else
	#successful execution
	email_body="Transfer of the folder '$source_dir' completed SUCCESSFULLY. See attached log file for details."
	subject="Subject: SUCCESSFUL completion of the transfer of files for directory: "$(basename $source_dir)
fi

if [ "$send_email_flag" == "True" ]; then
    #send email
    echo "$(date +"%Y-%m-%d %H:%M:%S")-->Preparing to send status email."  | tee -a "$transfer_log_file"
    echo "$(date +"%Y-%m-%d %H:%M:%S")-->smtp = "$smtp "; to_email = "$to_emails "; from_email = "$from_email | tee -a "$transfer_log_file"
    #swaks --server "$smtp" --to "$to_emails" --from "$from_email" --header "$subject"  --add-header "MIME-Version: 1.0" --add-header "Content-Type: text/html" --body "$email_body" --attach-type text/html --attach "$file" --attach-type text/html --attach "$REQ_LOG_FILE" $error_log_path
    if ! swaks --server $smtp --to $to_emails --from $from_email --header "$subject"  --add-header "MIME-Version: 1.0" --add-header "Content-Type: text/html" --body "$email_body" $attch_req_log | tail -n 4  | tee -a "$transfer_log_file" ; then
        echo "$(date +"%Y-%m-%d %H:%M:%S")-->Unexpected error occurred during sending status email." | tee -a "$transfer_log_file"
    fi
else
    echo "$(date +"%Y-%m-%d %H:%M:%S")-->Not sending and email because 'send_email_flag' was not set to 'True'."  | tee -a "$transfer_log_file"
fi
