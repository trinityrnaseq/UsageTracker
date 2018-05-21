#!/bin/bash

# Written by H.E. Cicada Brokaw Dennis
# December 2016

#WebsitePIDs=($(cat WebsitePID.txt))
#echo "killing ${WebsitePIDs[*]}"
#kill ${WebsitePIDs[0]}
# Following was not needed if the first one was the right one.
##kill ${WebsitePIDs[1]}

# Changed not to store the PID, but rather to figure out which PID's to kill.
# This is because of the file getting out of sync sometimes, so the kill did
# not end up killing the right PID's and then when the website gets restarted
# there are still previous website processes runnning, which creates a
# conflicting situation.

# So all PID's which are named "python trinity.py" will get killed now.
# For now that works, but could get us into trouble later on, because of the
# process being named "trinity.py". Need a better name for it, I think.

PIDs=($(ps aux | grep "trinity.py" | grep -v "grep"| tr -s [:blank:] " " | cut -d " " -f 2 | tr "\n" " "))
command_names=($(ps aux | grep "trinity.py" | grep -v "grep" | tr -s [:blank:] " " | cut -d " " -f 11 | tr "\n" " "))
arguments=($(ps aux | grep "trinity.py" | grep -v "grep" | tr -s [:blank:] " " | cut -d " " -f 12 | tr "\n" " "))
num_commands=${#command_names[*]}
echo "WebsiteStopper.sh found ${num_commands} potential command(s) to stop."
for (( i=0; i<${num_commands}; i += 1 ))
do
    if [[ ( "${arguments[${i}]}" == "trinity.py" ) ]]
    then
        if [[ ( "${command_names[${i}]}" == "python" ) || ( "${command_names[${i}]}" == "/usr/bin/python" ) ]]
        then
            echo "Killing pid ${PIDs[${i}]} ${command_names[${i}]} ${arguments[${i}]}"
            kill ${PIDs[${i}]}
        fi
    fi
done
