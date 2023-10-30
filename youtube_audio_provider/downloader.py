#!/usr/bin/python3
# -*- coding: utf-8 -*-

import subprocess
import json
import logging

logger = logging.getLogger(__name__)


class Downloader(object):

    def __init__(self, config, info):
        self.ffmpeg_location = config.get('ffmpeg_location')
        self.audio_path = config.get('audio_path', 'audio')
        self.appinfo = info
        self.downloader = self._determine_downloader()

    class Ytdlp:

        def __init__(self, ffmpeg_location, info):
            self.ffmpeg_location = ffmpeg_location

        def get_name(self):
            return "yt-dlp"

        def is_available(self):
            try:
                res = subprocess.check_output(["yt-dlp", "--version"])
                return res
            except:
                return False

        def find_youtube_id(self, search_string):
            params = ['yt-dlp', 'ytsearch:' + search_string, '--get-id']
            result = subprocess.run(params, capture_output=True, encoding='utf-8')
            return str(result.stdout).rstrip("\n")

        def find_youtube_info(self, search_string):
            params = ['yt-dlp', 'ytsearch:' + search_string, '-j']
            result = subprocess.run(params, capture_output=True, encoding='utf-8')
            j = json.loads(str(result.stdout).rstrip("\n"))
            return {
                "id": j['id'],
                "title": j.get('title', None),
                "channel": j.get('channel', None)
            }

        def download_youtube_id_to(self, id, destination_path):
            params = ['yt-dlp', '-x',
                '-N', ' 4',
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
                logger.error("failure running yt-dlp %s" % result.stderr)
            logger.debug("yt-dlp stdout %s" % result.stdout)
            
            start_str = '[ExtractAudio] Destination: '
            start_idx = result.stdout.find(start_str) + len(start_str)
            end_idx = result.stdout.find('\n', start_idx)
            
            content = result.stdout[start_idx:end_idx]
            # cut out the path = cut out length of path
            file_only = content[len(destination_path):].strip('\\/')
            return file_only

    class YoutubeDl:

        def __init__(self, ffmpeg_location, info):
            self.ffmpeg_location = ffmpeg_location
            self.info = info
        
        def get_name(self):
            return "youtube-dl"

        def is_available(self):
            try:
                res = subprocess.check_output(["youtube-dl", "--version"])
                return res
            except:
                return False

        
        def find_youtube_id(self, search_string):
            params = ['youtube-dl',
            'ytsearch:' + search_string,
            '--get-id']
            result = subprocess.run(params, capture_output=True, encoding='utf-8')

            return str(result.stdout).rstrip("\n")

        def find_youtube_info(self, search_string):
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
            
        def download_youtube_id_to(self, id, destination_path):
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

    def _check_type(self, sometype):
        is_avail_out = sometype.is_available()
        if (is_avail_out):
            logger.info("using " + sometype.get_name())
            self.appinfo.register("using", sometype.get_name())
            is_avail_out_printable = is_avail_out.decode("utf-8").strip()
            is_avail_out_printable = is_avail_out_printable.replace('\\r', '')
            is_avail_out_printable = is_avail_out_printable.replace('\\n', '')
            
            self.appinfo.register("version", is_avail_out_printable)
            return True
        return False

    def _determine_downloader(self):
        # check yt-dlp available
        y = Downloader.Ytdlp(self.ffmpeg_location, self.appinfo)
        if (self._check_type(y)):
            return y

        # check youtube-dl availability
        y = Downloader.YoutubeDl(self.ffmpeg_location, self.appinfo)
        if (self._check_type(y)):
            return y
        
        raise ValueError('cannot determine downloader.')

    def download_to_and_return_path(self, search_string):
        id = self.downloader.find_youtube_id(search_string)
        logger.debug("found youtube id %s, now downloading" % id)
        filename = self.downloader.download_youtube_id_to(id, self.audio_path)
        return filename

    def download_to_and_return_info(self, search_string):
        info = self.downloader.find_youtube_info(search_string)
        logger.debug("found youtube id %s, now downloading" % info['id'])
        logger.debug("additional info %s" % json.dumps(info, sort_keys=True, indent=4))
        filename = self.downloader.download_youtube_id_to(info['id'], self.audio_path)
        info['filename'] = filename
        return info
        

    