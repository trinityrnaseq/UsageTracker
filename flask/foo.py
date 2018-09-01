import sqlite3
import datetime

month_map = {'Jan': 1, 'Feb': 2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7,
    'Aug':8,  'Sep': 9, 'Oct':10, 'Nov': 11, 'Dec': 12}

def apache_date(s):
    return datetime.date(int(s[7:11]), month_map[s[3:6]], int(s[0:2]))

conn = sqlite3.connect('trinity.db')
c = conn.cursor()
c.execute(("select date, version from invocations"))
result = c.fetchall()

c.execute("""select tdate, count(distinct ip) from
                    (select substr(date,0,12) tdate, ip from invocations)
                  group by tdate order by tdate""");
by_ip = [[apache_date(r[0]), int(r[1])] for r in c.fetchall()]

conn.close()

print by_ip

