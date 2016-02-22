#!/usr/bin/python3

plex = '/mnt/plex'
plex_tv_ecuavisa = '%s/Media/TV/EcuaVisa' % plex
plex_media_scanner = '%s/Media/TV/EcuaVisa' % plex

noticieros_anteriores = 'http://www.ecuavisa.com/noticieros-anteriores'
noticieros_episode = 'http://www.ecuavisa.com/ajax-noticiero/nojs/%s/ampliado'
number_of_episodes_to_keep = 12

################################################

import datetime, io, os, re, subprocess, sys, time, traceback, urllib.request
import you_get, you_get.common, you_get.extractors

from contextlib import redirect_stdout
from stat import S_ISREG, ST_CTIME, ST_MODE
from subprocess import call

def logger(msg, log='sys', level='info', event_id='0x11800000'):
    if log != ('sys' or 'man' or 'conn'):
        log = 'sys'

    if level != ('info' or 'warn' or 'err'):
        level = 'info'

    print('[EcuaVisa]%s: %s' % (level, msg))
    # call(["synologset1", log, level, event_id, ('[EcuaVisa] %s' % msg)])

def month_str_to_int(month):
    if type(month) is int:
        return month

    months = [
        'enero',
        'febrero',
        'marzo',
        'abril',
        'mayo',
        'junio',
        'julio',
        'agosto',
        'septiembre',
        'octubre',
        'noviembre',
        'diciembre',
    ]

    return months.index(month) + 1

logger('Checking for New Episodes ...')
req = urllib.request.Request(noticieros_anteriores)
try:
    resp = urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    logger('HTTPError: %s' % e)


respData = resp.read()

episode_numbers = sorted(list(map(int, set(re.findall(r'ajax\-noticiero\/nojs\/([^\/]+)\/ampliado',str(respData))))), reverse=True)
logger('Found %s Episodes.' % len(episode_numbers))

os.chdir(plex_tv_ecuavisa)
downloaded_something = False

for i in list(range(number_of_episodes_to_keep)):
    req = urllib.request.Request(noticieros_episode % episode_numbers[i])
    try:
        resp = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        logger('HTTPError: %s' % e)
        continue

    respData = resp.read()

    url = (re.findall(r'<iframe(?:[^>]*)src="([^"]+)"',str(respData)))[0]
    logger('Downloading: %s' % url)

    # url = 'http://www.dailymotion.com/embed/video/x3qf80s?syndication=173592?inf  o=0&logo=0&related=0&'
    dm_info = {}
    with io.StringIO() as buf, redirect_stdout(buf):
        you_get.extractors.dailymotion.dailymotion_download(url, info_only=True)
        output = buf.getvalue().split('\n')

    for line in output:
        try:
            m = re.findall(r'(\w+):\s+(.+)', line)[0]
        except IndexError:
            pass
        dm_info[m[0]] = m[1]

    print(dm_info['Title'])

    ext = re.findall(r'\(video\/(\w+)\)', dm_info['Type'])[0]
    m = re.findall(r'(\w+)', dm_info['Title'])
    d = datetime.datetime(int(m[-1]), int(month_str_to_int(m[-2])), int(m[-3]))
    you_get.common.output_filename = 'EcuaVisa - '+ "{:%Y-%m-%d}".format(d) +' - '+ ' '.join(m[:-3]) +'.'+ ext

    if os.path.isfile(you_get.common.output_filename):
        logger('Skipping Downloaded: %s' % you_get.common.output_filename)
    else:
        try:
            download = you_get.extractors.dailymotion.dailymotion_download(url)
            downloaded_something = True
            logger('Downloaded: %s' % download)
        except:
            logger(traceback.format_exc(), level='err')

dirpath = r'.'

# get all entries in the directory w/ stats
entries = (os.path.join(dirpath, fn) for fn in os.listdir(dirpath))
entries = ((os.stat(path), path) for path in entries)

# leave only regular files, insert creation date
entries = ((stat[ST_CTIME], path)
           for stat, path in entries if S_ISREG(stat[ST_MODE]))
#NOTE: on Windows `ST_CTIME` is a creation date 
#  but on Unix it could be something else
#NOTE: use `ST_MTIME` to sort by a modification date

downloaded_episodes = list()
for cdate, path in sorted(entries, reverse=True):
    downloaded_episodes.append(path)


for i in list(range(number_of_episodes_to_keep, 999)):
    try:
        rm_this_file = downloaded_episodes[i]
    except IndexError:
        logger('Done looking for Old Episodes!')
        break

    logger('Deleting Old Episode: %s' % rm_this_file)

    try:
        os.remove(rm_this_file)
    except OSError:
        logger('Episode found a second ago, no longer exists. Moving on ...', level='warn')
        pass

if downloaded_something:
    os.environ['LD_LIBRARY_PATH'] = '/usr/lib/plexmediaserver'
    subprocess.check_call(['/usr/lib/plexmediaserver/Plex Media Scanner', '--scan', '--refresh', '--section', '1'])
