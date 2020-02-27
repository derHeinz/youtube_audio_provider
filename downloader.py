#!/usr/bin/python3
# -*- coding: utf-8 -*-

import subprocess

class Downloader(object):

    def __init__(self, ffmpeg_location):
        self.ffmpeg_location = ffmpeg_location

    def download_to(self, url, destination_path):
        params = ['youtube-dl', '-x', 
        '--audio-format', 'mp3', 
        '--audio-quality', '0', 
        '--ffmpeg-location', self.ffmpeg_location,
        '--playlist-start',
        '1',
        '--playlist-end',
        '1'
        ]
        
        if (destination_path != None):
            params.append('-o')
            params.append(destination_path + '/' + '%(title)s.%(ext)s')
        
        params.append(url)
        result = subprocess.run(params, capture_output=True, encoding='utf-8')
        
        # parse result
        # find [ffmpeg] Destination: <now the file begins> \r\n Deleting original file ....
        start_str = '[ffmpeg] Destination: '
        start_idx = result.stdout.find(start_str) + len(start_str)
        end_idx = result.stdout.find('\n', start_idx)
        
        content = result.stdout[start_idx:end_idx]
        # cut out the path = cut out length of path
        file_only = content[len(destination_path):].strip('\\/')
        return file_only
    