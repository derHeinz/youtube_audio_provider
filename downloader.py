#!/usr/bin/python3
# -*- coding: utf-8 -*-

import subprocess

class Downloader(object):

    def __init__(self, ffmpeg_location):
        self.ffmpeg_location = ffmpeg_location
        
    def find_youtube_id(self, search_string):
        params = ['youtube-dl',
        'ytsearch:' + search_string,
        '--get-id']
        result = subprocess.run(params, capture_output=True, encoding='utf-8')

        return str(result.stdout).rstrip("\n")
        
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
        
        start_str = '[ffmpeg] Destination: '
        start_idx = result.stdout.find(start_str) + len(start_str)
        end_idx = result.stdout.find('\n', start_idx)
        
        content = result.stdout[start_idx:end_idx]
        # cut out the path = cut out length of path
        file_only = content[len(destination_path):].strip('\\/')
        return file_only
 

    def download_to(self, search_string, destination_path):
       id = self.find_youtube_id(search_string)
       result = self.download_youtube_id_to(id, destination_path)
       return result
    