#/usr/bin/env python

""" webserver serving mp3 files for DLNA. """

import sys
import os
from threading import Thread
from flask import Flask, send_from_directory, make_response
from flask.json import jsonify
from werkzeug.serving import make_server

from urllib.parse import quote

class Webserver(Thread):

    def __init__(self, port, downloader):
        """Create a new instance of the flask app"""
        super(Webserver, self).__init__()

        # build up download path
        dir_path = os.path.dirname(os.path.realpath(__file__))
        audio_dir = os.path.join(dir_path, 'audio')

        self.audio_file_directory = audio_dir
        self.downloader = downloader

        self.app = Flask(__name__)
        self.app.config['port'] = port
        self.app.config['app_name'] = "Youtube Audio Provider"
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16mb is enough
        self.app.app_context().push()
        self._server = make_server(host='0.0.0.0', port=self.app.config['port'], app=self.app, threaded=True)
        print("Starting %s on port %d" % (self.app.config['app_name'], self.app.config['port']))

        # register some endpoints
        self.app.add_url_rule(rule="/", view_func=self.index, methods=['GET'])
        self.app.add_url_rule(rule="/audio/<path:path>", view_func=self.audio_file, methods=['GET'])
        self.app.add_url_rule(rule="/search/<string:search>", view_func=self.search, methods=['GET'])

        # register default error handler
        self.app.register_error_handler(code_or_exception=404, f=self.not_found)

    def run(self):
        self._server.serve_forever()

    def not_found(self, error):
        return make_response(jsonify({'error': 'Not found'}), 404)

    def index(self):
        """Serve the main index page"""
        return send_from_directory('static', 'index.html')
        
    def audio_file(self, path):
        """Serve files from the audio directory"""
        return send_from_directory('audio', path)
        
    def search(self, search):
        """search the string, return the url to the mp3."""
        # search_query_extended_for youtube_dl
        quoted_search = quote(search)
        base_url = "https://www.youtube.com/results?search_query="
        postfix = "&page=1"
        
        full_url = base_url + quoted_search + postfix
        
        # download via youtube-dl
        result =  self.downloader.download_to(full_url, self.audio_file_directory)
        
        # put together the new URL
        return '/audio/' + result
        