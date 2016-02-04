#!/usr/bin/python3

plex = '/volume1/homes/plex'
plex_tv_ecuavisa = '%s/Media/TV/EcuaVisa' % plex

noticieros_anteriores = 'http://www.ecuavisa.com/noticieros-anteriores'
noticieros_episode = 'http://www.ecuavisa.com/ajax-noticiero/nojs/%s/ampliado'
number_of_episodes_to_keep = 12

################################################

import os, re, sys, time, traceback, urllib.request

from stat import S_ISREG, ST_CTIME, ST_MODE
from subprocess import call
from you_get.common import *
from you_get.extractors import *
from you_get.common import *

def logger(msg, log='sys', level='info', event_id='0x11800000'):
    if log != ('sys' or 'man' or 'conn'):
        log = 'sys'

    if level != ('info' or 'warn' or 'err'):
        level = 'info'

    call(["synologset1", log, level, event_id, ('[EcuaVisa] %s' % msg)])

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

for i in list(range(number_of_episodes_to_keep)):
    req = urllib.request.Request(noticieros_episode % episode_numbers[i])
    try:
        resp = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        logger('HTTPError: %s' % e)

    respData = resp.read()

    url = (re.findall(r'<iframe(?:[^>]*)src="([^"]+)"',str(respData)))[0]
    logger('Downloading: %s' % url)
    try:
        download = dailymotion.dailymotion_download(url)
    except:
        logger(traceback.format_exc(), level='err')
        
    logger('Downloaded: %s' % download)

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
