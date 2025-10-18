#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
from contextlib import contextmanager
import yt_dlp

logger = logging.getLogger(__name__)


class Downloader(object):

    def __init__(self, config, info):
        self.ffmpeg_location = config.get('ffmpeg_location')
        self.audio_path = config.get('audio_path', 'audio')
        self.appinfo = info
        self.appinfo.register("downloader.name", "yt-dlp-python")
        self.appinfo.register("downloader.version", yt_dlp.version.__version__)

    class YtdlpPython:

        def __init__(self, ffmpeg_location):
            self.ffmpeg_location = ffmpeg_location

        def get_name(self):
            return "yt-dlp-python"
        
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
                'format': 'bestaudio/best',
                'noplaylist':True,
                'extract_flat': True,  # ← This is key! Only extracts minimal info like id, title, url
                'quiet': True
            }
            ydl_opts_download = {
                'format': 'bestaudio/best',
                'quiet': True,
                'concurrent_fragment_downloads': 4,
                'ffmpeg_location': self.ffmpeg_location,
                "outtmpl": destination_path + '/' + '%(title)s.%(ext)s',
                #'extractor_args': {'youtube': {'player_client': ['web']}}, -> may not be able to download all formats
                'extractor_args': {'youtube': {'skip': ['dash', 'hls', 'translated_subs']}},
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
                result['artist'] = first.get('artist', None)
                
                ydl.download([f"https://www.youtube.com/watch?v={id}"])

            file_only = final_filepath[len(destination_path):].strip('\\/')
            result['filename'] = file_only
            return result

    def download_to_and_return_path(self, search_string):
        info = self.downloader.download(search_string, self.audio_path)
        return info['filename']

    def download_to_and_return_info(self, search_string):
        info = self.downloader.download(search_string, self.audio_path)
        return info
    
    class DownloadContext:

        def _create_ydl_opts(self, destination_path: str, ffmpeg_location: str):
            def post_processor_hook(d):
                if d['status'] == 'finished':
                    # This is the final file after postprocessing
                    self.final_filepath = d['info_dict']['filepath']

            ydl_opts_extract_info = {
                'format': 'bestaudio/best',
                'noplaylist':True,
                'extract_flat': True,  # ← This is key! Only extracts minimal info like id, title, url
                'quiet': True
            }
            ydl_opts_download = {
                'format': 'bestaudio/best',
                'quiet': True,
                'concurrent_fragment_downloads': 4,
                'ffmpeg_location': ffmpeg_location,
                "outtmpl": destination_path + '/' + '%(title)s.%(ext)s',
                #'extractor_args': {'youtube': {'player_client': ['web']}}, -> may not be able to download all formats
                'extractor_args': {'youtube': {'skip': ['dash', 'hls', 'translated_subs']}},
                'postprocessors': [{  # Extract audio using ffmpeg
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                "postprocessor_hooks": [post_processor_hook]
            }
            # merge options for extract_info and for download:
            return ydl_opts_extract_info | ydl_opts_download

        def __init__(self, ffmpeg_location: str, destination_path: str, search_string: str):
            logger.info('constructing context')
            # store given parameters
            self.search_string = search_string
            self.destination_path = destination_path
            
            # prepare data
            self.final_filepath = None
            self.info = {}

            # create params
            ydl_opts = self._create_ydl_opts(self.destination_path, ffmpeg_location)
            self.ydl = yt_dlp.YoutubeDL(ydl_opts)

        def __enter__(self):
            self.ydl.__enter__()
            return self

        def __exit__(self, *args):
            self.ydl.__exit__(args)

        def get_id(self) -> str:
            logger.debug(f'retrieving id for {self.search_string}')
            all_info = self.ydl.extract_info(f"ytsearch:{self.search_string}", download=False)
            first = all_info['entries'][0]  # first entry (nearly always available)
            
            self.info['id'] = first['id']
            self.info['title'] = first.get('title', None)
            self.info['channel'] = first.get('channel', None)
            self.info['artist'] = first.get('artist', None)

            return self.info['id']
        
        def download(self):
            id = self.info['id']
            self.ydl.download([f"https://www.youtube.com/watch?v={id}"])

            file_only = self.final_filepath[len(self.destination_path):].strip('\\/')
            self.info['filename'] = file_only
            
            return self.get_info()
        
        def get_info(self):
            return self.info

    def create_download_context(self, search_string: str) -> DownloadContext:
        res = Downloader.DownloadContext(self.ffmpeg_location, self.audio_path, search_string)
        return res



