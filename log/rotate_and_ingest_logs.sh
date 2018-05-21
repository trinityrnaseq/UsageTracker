#!/bin/bash
# Rotate and Ingest nginx logs to compile Trinity Version information.
# Trinity software sends an http request to rt-trinity.uits.iu.edu in
# order to determine if it is the latest version. These requests are
# used to count invocations of Trinity around the world.

# This script written in May 2017 by H.E. Cicada Brokaw Dennis.
# It invokes the script ingest_logs.py, which requires certain
# sql packages to be installed.
# dot_local_lib_python2.7_MySQLdb.tar contains the MySQLdb package
# that is needed.
# One also needs to have defined in one's environment TRINITY_USER and TRINITY_PW.
# They are not defined in this script, as they are also used in other scripts.
# They are defined in the .bashrc files of users that are authorized to run these scripts.
# export TRINITY_USER='rt-trinity'
# export TRINITY_PW='place password here'
# FIX - Actually ingest_logs.py does not use those environment variable, but rather has
# the user name and password inside of the script. This should probably be changed. Too
# many points of failure if the password gets changed.

if [[ ( "$1" == "-h" ) || ( "$1" == "--help" ) || ( "$1" == "help" ) ]]
then
    echo "Usage: $0 [ rotate | ingest | help ]"
    echo "No argument rotates and ingests."
    echo "rotate does rotation and reopen of logs only."
    echo "ingest does ingest and backup of log only."
    echo "help prints this message."
    exit 1
fi

echo "Starting to rotate and ingest Trinity Version logs."
echo "System disk space:"
df

# Go to the directory where the logs are stored.
cd /web/log
err_val=0


if [[ "$1" != "ingest" ]]
then
    # Rotate the logs
    sudo logrotate logrotate.config
    err_val=$?
    if [[ ${err_val} -ne 0 ]]
    then
        echo "logrotate logrotate.config: call failed."
        exit ${err_val}
    fi
    echo "Successfully rotated logs."
    
    # Tell nginx to open new logs
    sudo nginx -s reopen
    err_val=$?
    if [[ ${err_val} -ne 0 ]]
    then
        echo "nginx -s reopen: call failed."
        exit ${err_val}
    fi
    echo "Successfully reopened logs."
fi

if [[ "$1" != "rotate" ]]
then
    # Ingest the log.
    python ingest_logs.py nginx.access.log.1
    err_val=$?
    if [[ ${err_val} -ne 0 ]]
    then
        echo "python ingest_logs.py nginx.access.log.1: call failed."
        exit ${err_val}
    fi
    echo "Successfully ingested most recent log."

    # Move the ingested log to the Karst logbackup directory.
    remote_filename="$(date +%Y_%m_%d.%s).ingested.log"
    # Use of -b causes sftp to abort if any of the input commands fail.
    printf "put nginx.access.log.1 trinity_admin/logbackup/${remote_filename}" | sftp -b - tstrnity@karst.uits.iu.edu
    err_val=$?
    if [[ ${err_val} -ne 0 ]]
    then
        echo "Transfering the file to tstrnity's Karst trinity_admin/logbackup failed."
        exit ${err_val}
    fi
    echo "Successfully backed up ingested log to Karst."
fi

exit $err_val
