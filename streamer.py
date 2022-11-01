#!/usr/bin/python

import subprocess
import sys

def show_help():
    print('Usage: ')
    print('./streamer.py url streamName destination')
    print('./streamer.py https://www.youtube.com/watch?v=9cQT4urTlXM streamName rtmp://192.168.88.59:1935/live')
    return
 
def streamer() :
    url = sys.argv[1]
    if not url :
        print('Error: url is empty')
        return
    stream_id = sys.argv[2]
    if not stream_id:
        print('Error: stream name is empty')
        return
    destination = sys.argv[3]
    if not destination:
        print('Error: destination is empty')
        return
 
    _youtube_process = subprocess.Popen(('youtube-dl','-f','','--prefer-ffmpeg', '--no-color', '--no-cache-dir', '--no-progress','-o', '-', '-f', '22/18', url, '--reject-title', stream_id),stdout=subprocess.PIPE)
    _ffmpeg_process = subprocess.Popen(('ffmpeg','-re','-i', '-','-preset', 'ultrafast','-vcodec', 'copy', '-acodec', 'copy','-threads','1', '-f', 'flv',destination + "/" + stream_id), stdin=_youtube_process.stdout)
    return
 
if len(sys.argv) < 4:
    show_help()
else:
    streamer()