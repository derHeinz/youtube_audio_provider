#!/usr/bin/python3
# -*- coding: utf-8 -*-

import subprocess
import json
import logging
from sys import stderr

logger = logging.getLogger(__name__)

class Downloader(object):

    def __init__(self, ffmpeg_location):
        self.ffmpeg_location = ffmpeg_location
        
    def _find_youtube_id(self, search_string):
        params = ['youtube-dl',
        'ytsearch:' + search_string,
        '--get-id']
        result = subprocess.run(params, capture_output=True, encoding='utf-8')

        return str(result.stdout).rstrip("\n")

    def _find_youtube_info(self, search_string):
        params = ['youtube-dl',
        'ytsearch:' + search_string,
        '-j']
        result = subprocess.run(params, capture_output=True, encoding='utf-8')

        j = json.loads(str(result.stdout).rstrip("\n"))
        return {
            "id": j['id'],
            "fulltitle": j.get('fulltitle', None),
            "title": j.get('title', None),
            "channel": j.get('channel', None)
        }
        
    def _download_youtube_id_to(self, id, destination_path):
        params = ['youtube-dl', '-x', 
        '--audio-format', 'mp3', 
        '--audio-quality', '0', 
        '--ffmpeg-location', self.ffmpeg_location]
        
        if (destination_path != None):
            params.append('-o')
            params.append(destination_path + '/' + '%(title)s.%(ext)s')
        
        # url that reads the id
        params.append('https://www.youtube.com/watch?v=' + id)
        result = subprocess.run(params, capture_output=True, encoding='utf-8')

        if (len(result.stderr) > 0):
            logger.error("failure running yoututbe-dl %s" % result.stderr)
        logger.debug("youtube-dl stdout %s" % result.stdout)
        
        start_str = '[ffmpeg] Destination: '
        start_idx = result.stdout.find(start_str) + len(start_str)
        end_idx = result.stdout.find('\n', start_idx)
        
        content = result.stdout[start_idx:end_idx]
        # cut out the path = cut out length of path
        file_only = content[len(destination_path):].strip('\\/')
        return file_only

    def download_to_and_return_path(self, search_string, destination_path):
       id = self._find_youtube_id(search_string)
       logger.debug("found youtube id %s, now downloading" % id)
       filename = self._download_youtube_id_to(id, destination_path)
       return filename

    def download_to_and_return_info(self, search_string, destination_path): #download_to_and_return_info
        info = self._find_youtube_info(search_string)
        logger.debug("found youtube id %s, now downloading" % info['id'])
        logger.debug("additional info %s" % json.dumps(info,sort_keys=True, indent=4))
        filename = self._download_youtube_id_to( info['id'], destination_path)
        info['filename'] = filename
        return info
        

    