#!/usr/bin/python3
import feedparser
import re
import datetime
import sys
import requests
import subprocess

DEBUG = 1

watchfile = '/srv/torrents/watch.list'
denyfile = '/srv/torrents/deny.list'
torrentsdir = '/mnt/storage/incoming/rt.pickup/'
logfile = '/srv/torrents/rss/downloaded.log'

#watchfile = '/srv/torrents/watch.list.tmp'          ################################
#torrentsdir = './'          ################################

now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

if (len(sys.argv) < 2):
    rssfeed='https://rarbgmirror.com/rssdd.php?category=18;41;49'
    try:
    	feedxml=requests.get(rssfeed)
    except:
        print("Unable to connect to feed.")
        sys.exit()
    feed = feedparser.parse(feedxml.text)
else:
    with open(sys.argv[1], 'r') as myfile:
        feedxml=myfile.read().replace('\\t','\t').replace('\\n','\n')
        feed = feedparser.parse(feedxml)

## LOAD WATCH LIST
watch = []
with open(watchfile) as ff1: 
    for ll in ff1:
        ll = ll.strip()
        if not re.match('^ *#', ll):
            tt = ll.split(';')
            if len(tt) == 4:
                size = tt[3]
            else:
                size = '1080p'
            tt.insert(0, re.compile('^(' + tt[2] + '.)(?:[(]?[0-9]{4}[)]?.)?([sS][0-9]{1,2}[eE][0-9]{1,2}).*' + size, re.IGNORECASE))
            watch.append(tt)

#DEBUG
#watch = [[re.compile('^(floribama.shore.)(?:[(]?[0-9]{4}[)]?.)?([sS][0-9]{1,2}[eE][0-9]{1,2}).*1080p',  re.IGNORECASE), 'floribama.shore', '1234', 'Floribama Shore']]

## LOAD DENY LIST
deny = []
with open(denyfile) as ff2:
    for ll in ff2:
        ll = ll.strip()
        if not re.match('^ *#', ll):
            deny.append(re.compile(ll, re.IGNORECASE))

## CYCLE THROUGH FEED

OUTSTR=""
OUTPUT = 0
COUNT = 0

for ff in feed.entries:
#    if DEBUG:
#        OUTSTR += '\nDEBUG eps: '+ ff.title +' | '+ ff.published          ################################
#        OUTPUT = 1
    COUNT += 1
    for series in watch:
        eps_re = series[0].match(ff.title)
        if eps_re:
            if DEBUG:
                OUTSTR += '\nDEBUG matched eps: '+ ff.title +' | '+ ff.published     ################################
                OUTPUT = 1
            if any(compiled_reg.match(ff.title) for compiled_reg in deny):
                if DEBUG:
                    OUTSTR += '\n\tdenied: ' + ff.title          ################################
                    OUTPUT = 1
                break
            else:
                if len(series) == 6:
                    eps = series[5] + '.' + eps_re[2]
                else:
                    eps = eps_re[1].replace(' ', '.') + eps_re[2]
                eps_re2 = re.search('(.*?)\.s([0-9]{1,2})e([0-9]{1,2})',  eps,  re.IGNORECASE)
                if eps_re2:
                    eps = "{}.S{:02d}E{:02d}".format(eps_re2[1],  int(eps_re2[2]),  int(eps_re2[3]))
                flag = 1
                with open(logfile) as lf:
                    for ll in lf:
                        if re.search(eps, ll, re.IGNORECASE):
#                            if DEBUG and COUNT < 2:
                            if DEBUG:
#                                OUTSTR += '\n\trepeat: ' + ff.title +' | '+ str(COUNT)      ################################
                                OUTPUT = 0  # if repeat, suppress DEBUG output
                            flag = 0
                            break
                if flag:
                    if DEBUG:
                        OUTSTR += '\n\tget: ' + ff.title      ################################
                        OUTPUT = 1
                    result=subprocess.check_output("deluge-console add '" + ff.link + "'",  shell=True)
                    if "Torrent added!" in result.decode("utf-8"):
                        if DEBUG:
                            OUTSTR += '\n\t\tBT OK: ' + ff.title          ################################
                            OUTPUT = 1
                        with open(logfile,  'a') as lf: 
                            lf.write(eps + ' %%%% ' + now + ' @' + ff.published + '\n')
                    else:
                        if DEBUG:
                            OUTSTR += '\n\t\tNOT ADDED:\n' +  result.decode("utf-8")     ################################
                            OUTPUT = 1
            break

if (len(sys.argv) < 2) and OUTPUT:
    print(OUTSTR)
#    print("\n\n<br>" + str(feedxml))
