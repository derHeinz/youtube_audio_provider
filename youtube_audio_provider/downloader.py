#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import importlib.util
import yt_dlp

logger = logging.getLogger(__name__)


class Downloader(object):

    def __init__(self, config, info):
        self.ffmpeg_location = config.get('ffmpeg_location')
        self.audio_path = config.get('audio_path', 'audio')
        self.appinfo = info
        self.downloader = self._determine_downloader()

    class YtdlpPython:

        def __init__(self, ffmpeg_location):
            self.ffmpeg_location = ffmpeg_location

        def get_name(self):
            return "yt-dlp-python"

        def is_available(self):
            return importlib.util.find_spec("yt_dlp") is not None
        
        def get_version(self):
            return yt_dlp.version.__version__
        
        def download(self, search_string, destination_path):
            final_filepath = None
            result = {}

            def post_processor_hook(d):
                if d['status'] == 'finished':
                    # This is the final file after postprocessing
                    nonlocal final_filepath
                    final_filepath = d['info_dict']['filepath']

            ydl_opts_extract_info = {
                'format': 'bestaudio',
                'noplaylist':True,
                'extract_flat': True,  # ← This is key! Only extracts minimal info like id, title, url
                'quiet': True
            }
            ydl_opts_download = {
                'format': 'bestaudio[ext=m4a]/bestaudio',
                'quiet': True,
                'concurrent_fragment_downloads': 4,
                'ffmpeg_location': self.ffmpeg_location,
                "outtmpl": destination_path + '/' + '%(title)s.%(ext)s',
                'extractor_args': {'youtube': {'player_client': ['web']}},
                'postprocessors': [{  # Extract audio using ffmpeg
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                "postprocessor_hooks": [post_processor_hook]
            }
            # merge options for extract_info and for download:
            ydl_opts = ydl_opts_extract_info | ydl_opts_download

            # only one context to omit duplicate resolution of information
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                all_info = ydl.extract_info(f"ytsearch:{search_string}", download=False)
                first = all_info['entries'][0]  # first entry (nearly always available)

                id = first['id']
                result['id'] = id
                result['title'] = first.get('title', None)
                result['channel'] = first.get('channel', None)
                
                ydl.download([f"https://www.youtube.com/watch?v={id}"])

            file_only = final_filepath[len(destination_path):].strip('\\/')
            result['filename'] = file_only
            return result

    def _check_type(self, sometype):
        is_avail_out = sometype.is_available()
        if (is_avail_out):
            logger.info("using " + sometype.get_name())
            self.appinfo.register("downloader.name", sometype.get_name())
            self.appinfo.register("downloader.version", sometype.get_version())
            return True
        return False

    def _determine_downloader(self):
        y = Downloader.YtdlpPython(self.ffmpeg_location)
        if (self._check_type(y)):
            return y
        
        raise ValueError('cannot determine downloader.')

    def download_to_and_return_path(self, search_string):
        info = self.downloader.download(search_string, self.audio_path)
        return info['filename']

    def download_to_and_return_info(self, search_string):
        info = self.downloader.download(search_string, self.audio_path)
        return info
