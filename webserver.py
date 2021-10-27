#/usr/bin/env python

""" webserver serving mp3 files for DLNA. """

import sys
import os
import json
import requests
from threading import Thread
from flask import send_from_directory, make_response, Response, stream_with_context
from flask.json import jsonify


from urllib.parse import quote

class Webserver(object):

    AUDIO_DIR_NAME = 'audio'
    AUDIO_DIR = '/' + AUDIO_DIR_NAME + '/'
    STREAM_NAME = 'audio_stream'
    STREAM = '/' + STREAM_NAME + '/'

    def __init__(self, flask_app, downloader, streamextractor, cache):
        """Create a new instance of the flask app"""
        super(Webserver, self).__init__()

        # build up download path
        dir_path = os.path.dirname(os.path.realpath(__file__))
        audio_dir = os.path.join(dir_path, 'audio')

        self.app = flask_app
        self.audio_file_directory = audio_dir
        self.downloader = downloader
        self.streamextractor = streamextractor
        self.cache = cache
        
        # register some endpoints
        self.app.add_url_rule(rule="/", view_func=self.index, methods=['GET'])
        self.app.add_url_rule(rule="/audio/<path:path>", view_func=self.audio_file, methods=['GET'])
        self.app.add_url_rule(rule="/search/<string:search>", view_func=self.search, methods=['GET'])

        # register default error handler
        self.app.register_error_handler(code_or_exception=404, f=self.not_found)

    def not_found(self, error):
        return make_response(jsonify({'error': 'Not found'}), 404)

    def index(self):
        """Serve the main index page"""
        return send_from_directory('static', 'index.html')
        
    def audio_file(self, path):
        if not self.cache.is_known(path):
            return make_response(jsonify({'error': 'Not found'}), 404)
        if not self.cache.is_stream(path):
            """Serve files from disk"""
            filename = self.cache.retrieve(path)
            return send_from_directory(self.AUDIO_DIR_NAME, filename)
        else:
            """Serve files by redirect"""
            url = self.cache.retrieve(path)
            r = requests.get(url, stream=True)
            return Response(r.iter_content(chunk_size=10*1024), content_type=r.headers['Content-Type'])

    def _download_audio(self, id, search):
        result_filename =  self.downloader.download_to(search, self.audio_file_directory)
            
        # put into cache
        self.cache.add_filename(id, result_filename)
        
    def search(self, search):
        """search the string, return the url to the mp3."""
        # search_query_extended_for youtube_dl
        quoted_search = quote(search)
        
        result = None
        cache_result = self.cache.retrieve_id_by_search(quoted_search)
        if (cache_result is not None):
            return self.AUDIO_DIR + str(cache_result)
        else:
            ## new style stream
            url = self.streamextractor.get_stream(quoted_search)
            new_id = self.cache.put_new_stream(quoted_search, url)
            
            ## start download, async
            new_download_thread = Thread(target=self._download_audio, args=(new_id, search), daemon=True)
            new_download_thread.start()
            
            return self.AUDIO_DIR + str(new_id)
