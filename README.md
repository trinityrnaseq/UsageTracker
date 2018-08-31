# UsageTracker
Tracks software version usage via URL ping

## Synopsis

This archive conatins all of the files that currently are utilized in maintaining the website that shows Trinity usage tracking information. As of August 25, 2018, this data was no longer collected. Trinity programs that were previously distributed will still attempt to check in, but the domain where they check in no longer exists. All supporting software also is no longer running.

## Model

Following is a description of how the data was collected for display. 
Requirements: 
    A virtual machine (VM) running RHEL6 with ngnix, PM2, python2.7, and flask. 
    A mysql database accessible from the VM. 

The extant Trinity software (up through versions 2.6 that I am aware of) send an http message with their ip address and Trinity Version to: rt-trinity.uits.iu.edu. That domain no longer exists. 

The messages are logged by the nginx server. 
Periodically, rotate_and_ingest_logs.sh, which is in the log directory, is run. 
It rotates the logs, then grabs the Trinity check in's out of the log file that was rotated out. 
The data is them placed into the database. 
The flask software uses templstes to create a graphic view of the data in the database. 
There are two views: 
    One has versions over time tallied by number of invocations. 
    One has versions over time tallied by number of ip addresses.

The flask web pages are also served by the nginx server.

There is no optimization, such that, as the quantity of data increases, the page takes longer and longer to load.
It would make sense, in a future configuration to store daily, weekly, and monthly tallies, in order to accelerate page loading behavior.

## Motivation

The desire was to see how various versions of Trinity were being used, in terms of numbers of runs, etc.

## Installation

The installation was unique and site-specific. Any new installation will need to be rewritten to handle the peculiarities of that installation. 
Also, the "check-in" behavior of Trinity would need to be modified to reach the new location, in some way. 
The database access would need to be modified to fit the needs of the db being used in the new location.

## Technical Notes

Flask is at https://www.fullstackpython.com/flask.html

Database Schema: trinity_versioncheck

```
mysql> show tables;
+--------------------------------+
| Tables_in_trinity_versioncheck |
+--------------------------------+
| build_components               |
| builds                         |
| galaxy_job                     |
| galaxy_statistic               |
| invocations                    |
| trinity_queue                  |
+--------------------------------+
```

The only table used for the Version Check information is invocations:

mysql> SELECT `COLUMN_NAME` from `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_SCHEMA`='trinity_versioncheck' AND `TABLE_NAME`='invocations';
```
+-------------+
| COLUMN_NAME |
+-------------+
| id          |
| timestamp   |
| ip_address  |
| version     |
| updated_at  |
| created_at  |
+-------------+
6 rows in set (0.00 sec)
```


In our version of the software, daily invocations of the following occured:
* /web/log/rotate_and_ingest_logs.sh calls ingest_log.py.
* /web/log/ingest_logs.py is the one that puts the data into the table.

And also, the flask procedure that displays the web page was https://rt-trinity.uits.indiana.edu/flask/calls/monthly

    /web/flask/trinity.py
        select distinct ip_address from invocations;
	    "select {0}, version, count(1) from invocations group by {0}, version".format(group)
	    "select {0}, version, count(distinct ip_address) from invocations group by {0}, version order by {0}".format(group)

## Contributors

Ben Fulton

H.E. Cicada Brokaw Dennis

The author of Trinity is Brian Haas.

## License

Unknown.
=======
>>>>>>> 63ff4975d9d2be59ea9554285dad7fb154ed0add
