#/usr/bin/env python

""" webserver serving mp3 files for DLNA. """

import sys
import os
import json
from json.decoder import JSONDecodeError
from threading import Thread
from flask import Flask, send_from_directory, make_response
from flask.json import jsonify
from werkzeug.serving import make_server

from urllib.parse import quote

class Webserver(Thread):

    AUDIO_DIR_NAME = 'audio'
    AUDIO_DIR = '/' + AUDIO_DIR_NAME + '/'

    def __init__(self, port, downloader, exporter):
        """Create a new instance of the flask app"""
        super(Webserver, self).__init__()

        # build up download path
        dir_path = os.path.dirname(os.path.realpath(__file__))
        audio_dir = os.path.join(dir_path, 'audio')

        self.audio_file_directory = audio_dir
        self.downloader = downloader
        self.exporter = exporter
        self.cachefile = os.path.join(os.path.dirname(__file__), "cache.json")
        self.cache = {}
        self._load_cache()
        self.exporter.export()

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

    def _retrieve_from_cache(self, quoted_search):
        # gets value from cache, checks whether file is available, otherwise invalidates cache
        
        # assert cache is loaded.
        simplified_string = quoted_search.casefold()

        if (self.cache != None and simplified_string in self.cache):
            print("cache hit for '{}'".format(simplified_string))
            cached_filename = self.cache[simplified_string]
            # check file exists:
            full_path = os.path.join(self.audio_file_directory, cached_filename)
            print("looking for file '{}'".format(full_path))
            if (os.path.exists(full_path)):
                return cached_filename
        return None
        
    def _put_to_cache(self, quoted_search, filename): 
        # put into cache the quoted_search string together with the filename
        
        # assert cache is loaded and no cache hit
        simplified_string = quoted_search.casefold()
        
        # put value to cache
        self.cache[simplified_string] = filename
        print("putting into cache '{}'".format(simplified_string))
        
        # persist into cachefile for restart
        with open(self.cachefile, 'w') as outfile:
            json.dump(self.cache, outfile)
        
    def _load_cache(self):
        # extract cache from persistent cache file
        with open(self.cachefile) as data_file:
            try:
                self.cache = json.load(data_file)
            except JSONDecodeError:
                pass

    def run(self):
        self._server.serve_forever()

    def not_found(self, error):
        return make_response(jsonify({'error': 'Not found'}), 404)

    def index(self):
        """Serve the main index page"""
        return send_from_directory('static', 'index.html')
        
    def audio_file(self, path):
        """Serve files from the audio directory"""
        return send_from_directory(self.AUDIO_DIR_NAME, path)
        
    def search(self, search):
        """search the string, return the url to the mp3."""
        # search_query_extended_for youtube_dl
        quoted_search = quote(search)
        
        result = None
        cache_result = self._retrieve_from_cache(quoted_search)
        if (cache_result is not None):
            result = cache_result
        else:
            # download via youtube-dl
            result =  self.downloader.download_to(full_url, self.audio_file_directory)
            
            # put into cache
            self._put_to_cache(quoted_search, result)
            self.exporter.export()
            
        # put together the result URL
        return self.AUDIO_DIR + result
        