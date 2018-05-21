#!/bin/bash

# Written by H.E. Cicada Brokaw Dennis
# Dec. 2016 - Jan 2017

# This program is intended to run in the background and requires the
# scripts: WebsiteStarter.sh and WebsiteStopper.sh.
# If the website does not return an OK status, 
#     It sends me an email,
#     it stops the current process associated with the website page,
#     then it starts a new process to create the website page.

# FIX - by adding command line arguments, the 3 scripts could be
# combined into one. An argument could also be made for writing this
# script in python instead of bash. However, as of 1/2017 the plan
# is to move the contents of the site into the rt-stats trinity
# pages, in which case, this script will not be needed. This
# script was a quick an dirty method of trying to make sure that
# the website was kept working. There was a problem with it periodically
# becoming unresponsive. Killing the process and restarting it
# "fixes" the problem.

cd /web/flask
while [ 1 ]
do
    # We don't check the website on maintenance days,
    # since the sql vm (rdc04.uits.iu.edu) can be down on that day.
    # So the website check is only done if it is not the first Tuesday 
    # or it is before 5am or after 7pm.
    # Meaning that it does not run the check on maintenance day between 5am and 7pm.
    DayOfTheWeek=`date +%-u`
    DayOfTheMonth=`date +%-d`
    HourOfTheDay=`date +%-k`
    if [[ ( HourOfTheDay -lt 5 )  || ( HourOfTheDay -gt 19 ) || ( ! ( (DayOfTheWeek -eq 2) && (DayOfTheMonth -le 7) ) ) ]] 
    then
        curl -I http://rt-trinity.uits.indiana.edu/flask/calls/monthly > WebsiteChecker.txt
        StatusLine=($(head -n 1 WebsiteChecker.txt | tr [:blank:] " "))
        # In the following, there is a <CR> that is not getting translated into a space,
        # that is getting left on the end of the 3rd element in StatusLine. So for that
        # element, we only check the first two characters of the element.
        if [[ ( "${StatusLine[0]}" != "HTTP/1.1" ) || ( "${StatusLine[1]}" != "200" ) || ( "${StatusLine[2]:0:2}" != "OK" ) ]]
        then
            /bin/date
            echo "Trinity Versions webpage is not OK!"
            echo ${StatusLine[*]}
            echo "Trinity Versions webpage is not OK!" > WebsiteCheckerEmail.txt
            echo "Following is the flask website's current status" >> WebsiteCheckerEmail.txt
            echo "" >> WebsiteCheckerEmail.txt
            cat WebsiteChecker.txt >> WebsiteCheckerEmail.txt
            mail -s "Trinity Versions Website Down" hbrokaw@iu.edu < WebsiteCheckerEmail.txt
            # kill any outstanding python trinity commands.
            ./WebsiteStopper.sh
            # Give one minute for processes and subprocesses to stop running.
            sleep 60
            # Start the webpage again.
            ./WebsiteStarter.sh
            # Wait one hour after starting the webpage before checking again.
            # That way, if there is some other problem with the network that
            # is causing the problem, I only get email once per hour at most.
            sleep 3600
        else
            /bin/date
            echo ${StatusLine[*]}
        fi
    fi
    # Sleep two minutes, meaning we only check the website once every 2 minutes.
    sleep 120
done
