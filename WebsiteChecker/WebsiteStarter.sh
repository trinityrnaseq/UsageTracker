#!/bin/bash

# Written by H.E. Cicada Brokaw Dennis
# December 2016

# We have to use the python that is in /usr/bin to run this script, because that is
# the one that has the Flask module in it.
nohup /usr/bin/python trinity.py >& trinity.py.output.txt &
# nohup /usr/local/bin/python2.7 trinity.py >& trinity.py.output.txt &
echo "Process status after restarting Trinity Versions website:"
ps aux | grep "trinity.py" | grep -v "grep"
echo ""

# No longer trying to store the PID, because other events can cause it to be
# stale. The WebsiteStopper.sh now finds the process by "deduction".

# website_pid=$!
# sleep 60
##echo $website_pid > WebsitePID.txt
# It turns out that the process started by the nohup command
# above actually strts up another python process that actually does 
# the work. So killing the website_pid process does not stop the website
# from running. The below command finds both processes, and the 14th
# field of the resulting array is the pid of the spawned process.
# Killing that process successfully terminates both processes. 
# ProcessInfo=($(ps aux | grep hbrokaw | grep trinity))
# echo ${ProcessInfo[13]} > WebsitePID.txt
