#/usr/bin/env python

""" webserver serving mp3 files for DLNA. """

import sys
import os
import json
import requests
import subprocess
from threading import Thread
from flask import send_from_directory, make_response, Response, stream_with_context
from flask.json import jsonify
from flask import Flask
from werkzeug.serving import make_server
from urllib.parse import quote

class Webserver(object):

    AUDIO_DIR_NAME = 'audio'
    AUDIO_DIR = '/' + AUDIO_DIR_NAME + '/'
    STREAM_NAME = 'audio_stream'
    STREAM = '/' + STREAM_NAME + '/'

    def __init__(self):
        """Create a new instance of the flask app"""
        super(Webserver, self).__init__()

        self.app = Flask(__name__)
        self.app.config['port'] = 1234
        self.app.config['app_name'] = "Webserved Streamer"
        #app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16mb is enough for posts
        
        self.app.app_context().push()
        
        # register some endpoints
        self.app.add_url_rule(rule="/audio/<path:path>", view_func=self.audio_file, methods=['GET'])

        
    def audio_file(self, path):
        """Serve files by redirect"""
        _youtube_process = subprocess.Popen(('youtube-dl','-f','','--prefer-ffmpeg', '--no-color', '--no-cache-dir', '--no-progress','-o', '-', '-f', '22/18', url, '--reject-title', stream_id),stdout=subprocess.PIPE)
    _ffmpeg_process = subprocess.Popen(('ffmpeg','-re','-i', '-','-preset', 'ultrafast','-vcodec', 'copy', '-acodec', 'copy','-threads','1', '-f', 'flv',destination + "/" + stream_id), stdin=_youtube_process.stdout)
        
        url = self.cache.retrieve(path)
        r = requests.get(url, stream=True)
        return Response(r.iter_content(chunk_size=10*1024), content_type=r.headers['Content-Type'])


ws = Webserver()

server = make_server(host='0.0.0.0', port=ws.app.config['port'], app=ws.app, threaded=True)
print("Starting %s on port %d" % (ws.app.config['app_name'], ws.app.config['port']))
server.serve_forever() 
