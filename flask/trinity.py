#! /usr/bin/python

from flask import Flask, render_template, make_response, request
import sqlite3
from operator import itemgetter
from collections import namedtuple, defaultdict
import logging
from logging.handlers import RotatingFileHandler
import datetime
import MySQLdb
import os

display = namedtuple('display', 'color title marker')

app = Flask(__name__)


def db_connect():
    # Following change made 2018/05/20 by Cicada Dennis. I stopped using environment for TRINITY_USER
    # because I could not get the PM2 daemon to re-read the variable and did not know how to restart it.
    # The commented out was the old connection info. New connection as of 2018/05/17.
    # conn2 = MySQLdb.connect(host='rdc04.uits.iu.edu', port=3082, user=os.environ['TRINITY_USER'], passwd=os.environ['TRINITY_PW'],
    conn2 = MySQLdb.connect(host='sasrdsmp01.uits.iu.edu', port=3306, user='trinity_rt-trinity', passwd=os.environ['TRINITY_PW'], db='trinity_versioncheck')
    return conn2


@app.route("/flask")
def hello(chartID = 'chart_ID', chart_type = 'bar', chart_height = 350):
    data = load_component_timings()
    datasets = ['Dme7g', 'Dme5g', 'Dme3g', 'Dme1g', 'Dme500m']
    charts = []
    for dataset in datasets:
        series_data = (line for line in data if line[1] == dataset)
        series = [build_series(line) for line in series_data]
        charts.append(dict(series=series, dataset=dataset))

    return render_template("chart.html",charts=charts)

@app.route('/download')
def download():
    data = load_component_timings()
    header =  ("version,dataset,fastool,jellyfish,inchworm,bowtie_build,bowtie,sort,graphfromfasta,"
               "readstotranscripts,chrysalis,quantifygraph,butterfly\n")
    data = "\n".join((",".join((str(i) if i else '' for i in line)) for line in data))
    response = make_response(header+data)
    response.headers["Content-Disposition"] = "attachment; filename=trinity.csv"
    return response

@app.route("/inchworm")
def inchworm():
    conn = sqlite3.connect('inchworm.db')
    c = conn.cursor()
    c.execute(("select system, dataset, description, nodes, value from jobs"))
    result = c.fetchall()
    conn.close()
    d = set(r[0:2] for r in result)
    charts = []
    for table in sorted(sorted(d, key=itemgetter(0)), key=itemgetter(1), reverse=True):
        tdict=dict(cluster=table[0], dataset=table[1])
        series = set(r[2] for r in result if r[0] == table[0] and r[1] == table[1])
        mydict = dict()
        for xx in series:
            data = (r[3:5] for r in result if r[0] == table[0] and r[1] == table[1] and r[2] == xx)
            mydict[xx] = ["[%s,%s]" % z for z in data]
        tdict['series'] = mydict
        if tdict['dataset'] == 'Schizo':
            tdict['datasize'] = '500M'
        elif tdict['dataset'] == 'Mouse':
            tdict['datasize'] = '1.5G'
        charts.append(tdict)
    return render_template("inchworm.html", charts=charts)


def format_timings(component_list, time_list):
    timings = dict([r[0], r[1]] for r in time_list)
    ordered = (timings[c] if c in timings else 0 for c in component_list)
    formatted = ",".join(str(r) for r in ordered)
    return formatted


@app.route("/buildtimings")
def buildtimings():
    conn = db_connect()
    c = conn.cursor()

    #old_series = _get_old_series(c)
    c.execute(("select build_id, id, runtime_seconds from builds where date = (select max(date) from builds)"))
    build_info = c.fetchone()

    c.execute("select name, bc.runtime_seconds from build_components bc where build_id = %s", build_info[1])
    most_recent = c.fetchall()

    c.execute("select name, avg(runtime_seconds) from build_components bc group by name")
    average = c.fetchall()
    conn.close()

    component_list = ['fastool', 'jellyfish', 'inchworm', 'bowtie-build', 'bowtie', 'samtools_view', 'samtools_sort',
        'scaffold_iworm_contigs', 'sort', 'FastaToDeBruijn', 'GraphFromFasta', 'ReadsToTranscripts',
        'Chrysalis', 'partition_chrysalis_graphs_n_reads', 'QuantifyGraph', 'Parafly', 'Butterfly', 'scaffold',
        'Print_Butterfly_Assemblies', 'fasta_filter_by_min_length', 'cat', 'createiwormfastabundle', 'exittester',
        'samtools', 'partitioned_trinity_aggregator']

    recent_str = format_timings(component_list, most_recent)
    average_str = format_timings(component_list, average)

    return render_template("build_timings.html",latest=recent_str, average=average_str, components=component_list, buildname=build_info[0])#, old_series=old_series)


@app.route("/charts")
def charts():
    pass


month_map = {'Jan': 1, 'Feb': 2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7,
    'Aug':8,  'Sep': 9, 'Oct':10, 'Nov': 11, 'Dec': 12}


def apache_date(s):
    return datetime.date(int(s[7:11]), month_map[s[3:6]], int(s[0:2]))


def get_grouping(grouping):
    group = 'date(timestamp)'
    date_func = lambda d: d
    if grouping == 'weekly':
        group = 'yearweek(timestamp)'
        date_func = lambda d: datetime.datetime.strptime(str(d) + '1', '%Y%W%w')
    if grouping == 'monthly':
        group = "DATE_FORMAT(timestamp, '%Y%m')"
        date_func = lambda d: datetime.datetime.strptime(str(d) + '1', '%Y%m%w')
    return date_func, group


@app.route("/calls")
@app.route("/calls/<grouping>")
def calls(grouping=None):
    conn2 = db_connect()
    c = conn2.cursor()
    date_func, group = get_grouping(grouping)

    c.execute("select {0}, version, count(1) from invocations group by {0}, version".format(group))
    result = c.fetchall()

    c.execute("select {0}, version, count(distinct ip_address) from invocations group by {0}, version order by {0}".format(group));
    by_ip = c.fetchall()
    conn2.close()

    data = build_version_series(date_func, result)
    data2 = build_version_series(date_func, by_ip)

    return render_template("calls.html", categories=sorted(data.keys()), values=data, by_ip=data2)


def build_version_series(date_func, result):
    versions = set(r[1] for r in result)
    call_count = dict([v, defaultdict(int)] for v in versions)
    for r in result:
        dt = date_func(r[0])
        version = r[1]
        call_count[version][dt] = r[2]
    data = dict([k, v.iteritems()] for k, v in call_count.iteritems())
    return data

@app.route("/version/<trinity_version>")
def version(trinity_version):
    if 'timestamp' in request.args:
        ts = request.args['timestamp']
    else:
        ts = ''

    if trinity_version == 'BLEEDING_EDGE':
        result = 'yes'
    else:
        result = 'BLEEDING_EDGE'

    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    # Log timestamp, remote address, remote timestamp, remote version, response
    app.logger.info(','.join([str(datetime.datetime.utcnow()), ip, ts, trinity_version, result]))
    return result

def load_component_timings():
    conn = sqlite3.connect('trinity.db')
    c = conn.cursor()
    c.execute(("select version, dataset, fastool, jellyfish, inchworm, bowtie_build, bowtie, sort, graphfromfasta, "
                    "readstotranscripts, chrysalis, quantifygraph, butterfly from jobs"))
    result = c.fetchall()
    conn.close()
    return result

def build_series(data):
    # colors selected from http://www.colorcombos.com/color-schemes/124/ColorCombo124.html
    display_dict = {
        '2012-10-05': display('#E8D0A9', '2012 October', 'circle'),
        '2013-02-25': display('#B7AFA3', '2013 February', 'square'),
        '2013_08_14': display('#C1DAD6', '2013 August', 'diamond'),
        'November': display('#a2d0d0', '2013 November', 'triangle'),
        'April': display('#ACD1E9', '2014 April', 'triangle-down'),
        '20140714': display('#6D929B', '2014 July', 'circle')
    }
    disp = display_dict[data[0]]
    return dict(name=disp.title,
                       marker=dict(symbol=disp.marker),
                       color=disp.color,
                       data=[int(i) if i else 0 for i in data[2:]])

if __name__ == "__main__":
    handler = RotatingFileHandler('trinity_version.log', maxBytes=100000, backupCount=10)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(debug=True)

