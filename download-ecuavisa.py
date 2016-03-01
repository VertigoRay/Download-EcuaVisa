#!/usr/bin/python3

plex = '/mnt/plex'
plex_media_scanner = '/usr/lib/plexmediaserver/Plex Media Scanner'
plex_media_scanner_section = '1'
plex_LD_LIBRARY_PATH = '/usr/lib/plexmediaserver'

plex_tv_ecuavisa = '%s/Media/TV/EcuaVisa' % plex
plex_tv_ecuavisa_televistazo = '%s/Televistazo' % plex_tv_ecuavisa
plex_tv_ecuavisa_telemundo = '%s/Telemundo' % plex_tv_ecuavisa

televistazo = 'http://www.dailymotion.com/rss/user/ecuavisa/lang/es/search/Televistazo/1'
telemundo = 'http://www.dailymotion.com/rss/user/ecuavisa/lang/es/search/Telemundo/1'

number_of_televistazo_episodes_to_keep = 6
number_of_telemundo_episodes_to_keep = 6

################################################

import datetime, feedparser, io, os, re, subprocess, sys, time, traceback
import you_get, you_get.common, you_get.extractors

from contextlib import redirect_stdout
from pathlib import Path
from stat import S_ISREG, ST_CTIME, ST_MODE
from subprocess import call

def logger(msg, log='sys', level='info', event_id='0x11800000'):
    if log != ('sys' or 'man' or 'conn'):
        log = 'sys'

    if level != ('info' or 'warn' or 'err'):
        level = 'info'

    print('[EcuaVisa]%s: %s' % (level, msg))
    # call(["synologset1", log, level, event_id, ('[EcuaVisa] %s' % msg)])

def cleanup(number_of_episodes_to_keep, dirpath=r'.'):
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


def download(url):
    # url = 'http://www.dailymotion.com/embed/video/x3qf80s'
    dm_info = {}
    with io.StringIO() as buf, redirect_stdout(buf):
        you_get.extractors.dailymotion.dailymotion_download(url, info_only=True)
        output = buf.getvalue().split('\n')
    #        
    for line in output:
        try:
            m = re.findall(r'(\w+):\s+(.+)', line)[0]
        except IndexError:
            pass
        dm_info[m[0]] = m[1]

    print(dm_info['Title'])

    ext = re.findall(r'\(video\/(\w+)\)', dm_info['Type'])[0]
    m = re.findall(r'(\w+)', dm_info['Title'])
    
    title = ' '.join(m[:-3])

    if m[-3] == 'Telemundo':
        d = datetime.datetime(datetime.datetime.now().year, int(month_str_to_int(m[-1])), int(m[-2]))
        title = ' '.join(m[:-2])
    elif m[-2] == 'de':
        d = datetime.datetime(datetime.datetime.now().year, int(month_str_to_int(m[-1])), int(m[-3]))
    else:
        try:
            d = datetime.datetime(int(m[-1]), int(month_str_to_int(m[-2])), int(m[-3]))
        except ValueError:
            d = datetime.datetime(int(m[-1]), int(month_str_to_int(m[-3])), int(m[-2]))

    you_get.common.output_filename = 'EcuaVisa - '+ "{:%Y-%m-%d}".format(d) +' - '+ title +'.'+ ext

    if os.path.isfile(you_get.common.output_filename):
        logger('Skipping Downloaded: %s' % you_get.common.output_filename)
    else:
        try:
            download = you_get.extractors.dailymotion.dailymotion_download(url)
            logger('Downloaded: %s' % download)
            return True
        except:
            logger(traceback.format_exc(), level='err')
            return False


def month_str_to_int(month):
    if type(month) is int:
        return month

    try:
        return int(month)
    except ValueError:
        pass

    months = {
        'enero': 1,
        'febrero': 2,
        'marzo': 3,
        'abril': 4,
        'mayo': 5,
        'junio': 6,
        'julio': 7,
        'agosto': 8,
        'septiembre': 9,
        'octubre': 10,
        'noviembre': 11,
        'diciembre': 12,
    }

    return months[month]

if os.path.exists('/tmp/ecuavista-downloading'):
    exit()

Path('/tmp/ecuavista-downloading').touch()

logger('Checking for New Episodes ...')
feed_televistazo = feedparser.parse( televistazo )
feed_telemundo = feedparser.parse( telemundo )

downloaded_something = False

try: 
    os.makedirs(plex_tv_ecuavisa_televistazo)
except OSError:
    if not os.path.isdir(plex_tv_ecuavisa_televistazo):
        raise

os.chdir(plex_tv_ecuavisa_televistazo)

i=0
for item in feed_televistazo['items']:
    i+=1
    downloaded = download(item['media_content'][0]['url'])
    if downloaded:
        downloaded_something = True

    if i == number_of_televistazo_episodes_to_keep:
        break

cleanup(number_of_televistazo_episodes_to_keep)


try: 
    os.makedirs(plex_tv_ecuavisa_telemundo)
except OSError:
    if not os.path.isdir(plex_tv_ecuavisa_telemundo):
        raise

os.chdir(plex_tv_ecuavisa_telemundo)
i=0
for item in feed_telemundo['items']:
    i+=1
    downloaded = download(item['media_content'][0]['url'])
    if downloaded:
        downloaded_something = True

    if i == number_of_telemundo_episodes_to_keep:
        break

cleanup(number_of_telemundo_episodes_to_keep)


if downloaded_something:
    os.environ['LD_LIBRARY_PATH'] = plex_LD_LIBRARY_PATH
    subprocess.check_call([plex_media_scanner, '--scan', '--refresh', '--section', plex_media_scanner_section])


os.remove('/tmp/ecuavista-downloading')
