#
# Written by Ben Fulton.
# Maintenance taken over by Cicada Dennis in Nov. 2016
# 
# 2016-12-16 Added code to account for versions that have the word "Trinity-"
# prepended to their version number.
#
# 2017-06-01 Added code to account for https 301 redirects in the request.
# Examples
# new lines look like:
# 164.67.172.73 - - [31/May/2017:00:52:34 -0400]  301 "GET /flask/version/Trinity-v2.4.0?timestamp=1496206355 HTTP/1.1" 185 "-" "curl/7.52.1" "-"
# 133.39.224.85 - - [31/May/2017:00:58:15 -0400]  301 "GET /flask/version/Trinity-v2.4.0?timestamp=1496206695 HTTP/1.1" 185 "-" "curl/7.19.7 (x86_64-redhat-linux-gnu) libcurl/7.19.7 NSS/3.14.0.0 zlib/1.2.6 libidn/1.18 libssh2/1.4.2" "-"
# whereas old lines look like:
# 212.250.134.248 - - [30/May/2017:05:46:05 -0400] "GET /flask/version/v2.2.0?timestamp=1496137565 HTTP/1.1" 200 13 "-" "curl/7.47.0"
# 133.39.224.30 - - [30/May/2017:05:47:20 -0400] "GET /flask/version/v2.1.1?timestamp=1496137639 HTTP/1.1" 200 13 "-" "curl/7.19.7 (x86_64-redhat-linux-gnu) libcurl/7.19.7 NSS/3.# 
#
# rt-trinity is now set to only allow https requests in.
# Examples
# requests now look like:
# 140.77.78.250 - - [30/May/2017:11:53:52 -0400]  301 "GET /flask/version/v2.2.0?timestamp=1496159632 HTTP/1.1" 185 "-" "curl/7.52.1" "-"
# whereas before the requests looked like:
# 140.77.78.250 - - [30/May/2017:11:53:40 -0400] "GET /flask/version/v2.2.0?timestamp=1496159618 HTTP/1.1" 200 13 "-" "curl/7.52.1"
#
# Newer versions of Trinity may change to use https, so we should maintain support for both forms.
#
import sqlite3
import sys
import re
import datetime
import MySQLdb

format_pat= re.compile(
    r"(?P<host>(?:[\d\.]|[\da-fA-F:])+)\s"
    r"(?P<identity>\S*)\s"
    r"(?P<user>\S*)\s"
    r"\[(?P<time>.*?)\]\s+"
    r"(?P<redirect>\d*)\s*"
    r'"(?P<request>.*?)"\s'
)

__author__ = 'befulton (modified by hbrokaw)'
__version__ = 3.0

month_map = {'Jan': 1, 'Feb': 2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul': 7,
    'Aug': 8,  'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

def apache_time(s):
    global month_hash
    return datetime.datetime(int(s[7:11]), month_map[s[3:6]], int(s[0:2]), \
         int(s[12:14]), int(s[15:17]), int(s[18:20]))


def parse_line(line):
    # print "Starting to look for match"
    match= format_pat.match(line)
    # print "Match is {:s}\n".format(str(match))
    # print line
    entry = None
    if match:
        d = match.groupdict()
        # if d['request'].startswith('GET /flask/version/v'):
        # if d['redirect'] == "301" \
        if d['request'].startswith('GET /flask/version/'):
            # print line
            version = d['request'].split(' ')[1][15:].split('?')[0]
            # print "{:s}\n".format(str(version))
            if (version[0:8] == "Trinity-"):
                version = version[8:]
                #print "changed to: {:s}\n".format(str(version))
            # Eliminate versions that are _PRERELEASE, __DEVEL_BRANCH__, __BLEEDING_EDGE__, etc.
            version_parts = version.split('_')
            if (len(version_parts) == 1):
                # There should only be one part when the version is a release version.
                # Sometimes one line will be written into the file over the contents of another
                # line. In some cases this can cause the version number to be messed up.
                # Detect such errors and throw an exception when they happen.
                if (len(version) > 6):
                    print "There is a version that is unknown:"
                    print "\t{:s}\n".format(str(version)) \
                            + "\t{:s}".format(line)
                num_parts = version_parts[0].split(".")
                # There should be 3 parts to the number.
                if (len(num_parts) != 3) or (num_parts[0][0] != "v") or (len(num_parts[2]) > 2):
                    raise ValueError("The version value ({:s}) does not seem to be valid.\n".format(version) \
                        + "\t{:s}".format(line))
                else:
                    # FIX - One could further verify that there are not other non-digit values (other than the leading 'v').
                    # and repair if possible (like the repair checking the final column which follows).
                    # I found one time an entry that had a trailing '/' at the end of the number.
                    # remove any such trailing slash (or other trailing non-digit character).
                    if not version_parts[0][-1].isdigit():
                        print "WARNING: version number has trailing non-digit: {:s}".format(str(version_parts[0]))
                        print "The entire line is:\n\t{:s}".format(line)
                        version_value = version_parts[0][:-1]
                    else:
                        version_value = version_parts[0]
                    # Check that the ip address is in the correct format.
                    # Sometimes one line will be written into the file over the contents of another
                    # line. In some cases this can cause the ip address to be messed up.
                    # Detect such errors and throw an exception when they happen.
                    ip_address = d['host'].split('.')
                    # print ip_address
                    if (len(ip_address) != 4) or (len({ip_part for ip_part in ip_address if (len(ip_part) > 3)}) > 0):
                        raise ValueError("The ip address of a host ({:s}) does not seem to be valid.\n".format(d['host']) \
                            + "\t{:s}".format(line))
                    try:
                        entry = apache_time(d['time']), d['host'], version_value
                    except:
                        print "Error while processing the line:\n\t{:s}".format(line)
                        print "\td is {:s}\n\tversion_value is {:s}".format(str(d), str(version_value))
                        raise
    return entry


def record(rows):
    print "Recording {:d} rows.".format(len(rows))
    # Database schema moved May 17, 2018. Cicada Dennis changed below line to new information.
    # conn2 = MySQLdb.connect(host='rdc04.uits.iu.edu', port=3082, user='rt-trinity', passwd='q8#F@qZ_&hXC3%mP', db='versioncheck')
    conn2 = MySQLdb.connect(host='sasrdsmp01.uits.iu.edu', port=3306, user='trinity_rt-trinity', passwd='q8#F@qZ_&hXC3%mP', db='trinity_versioncheck')
    c = conn2.cursor()
    print "Writing"
    c.executemany("""insert ignore into invocations
    (timestamp, ip_address, version, updated_at, created_at)
    values (%s, %s, %s, sysdate(), sysdate())""", rows)
    print "Committing"
    conn2.commit()


with open(sys.argv[1]) as f:
    print "Opened the file"
    entries = (parse_line(line) for line in f)
    # If the following print is used, then the entries object (a generator) gets used and 
    # a subsequent attempt to use it starts at the end of the list.
    # print "There are {:d} entries.".format(len(set(e for e in entries if e)))
    record(set(e for e in entries if e))
