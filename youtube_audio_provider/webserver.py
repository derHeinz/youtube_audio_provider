#!/usr/bin/python3
# -*- coding: utf-8 -*-

""" webserver serving mp3 files for DLNA. """

import os
import time
from threading import Thread
from flask import Flask, send_from_directory, make_response, abort
from flask.json import jsonify
from werkzeug.serving import make_server
from urllib.parse import quote
import logging

from youtube_audio_provider.cache import Cache
from youtube_audio_provider.downloader import Downloader
from youtube_audio_provider.exporter.cache_html_exporter import CacheHTMLExporter
from youtube_audio_provider.appinfo import AppInfo

logger = logging.getLogger(__name__)

class Webserver(Thread):

    AUDIO_DIR_NAME = 'audio'
    AUDIO_DIR = '/' + AUDIO_DIR_NAME + '/'

    def __init__(self, config, downloader: Downloader, exporter: CacheHTMLExporter, info: AppInfo):
        """Create a new instance of the flask app"""
        super(Webserver, self).__init__()

        self.audio_path = config.get('audio_path', 'audio')
        # TODO calculate audio_path as seen by flask with it's root_path: self.app.root_path
        info.register('audio_directory', os.path.abspath(self.audio_path))
        self.downloader = downloader
        self.exporter = exporter
        self.appinfo = info
        self.cache = Cache(exporter, info, self.audio_path)

        self.app = Flask(__name__)
        self.app.config['port'] = config['webserver_port']
        self.app.config['app_name'] = "Youtube Audio Provider"
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16mb is enough
        self.app.root_path
        self.app.app_context().push()
        self._server = make_server(host='0.0.0.0', port=self.app.config['port'], app=self.app, threaded=True)
        logger.info("Starting %s on port %d\nPress CTRL-C to exit" % (self.app.config['app_name'], self.app.config['port']))

        # register some endpoints
        self.app.add_url_rule(rule="/", view_func=self.index, methods=['GET'])
        self.app.add_url_rule(rule="/audio/<path:path>", view_func=self.audio_file, methods=['GET'])
        self.app.add_url_rule(rule="/delete_by_search/<string:search>", view_func=self.delete_by_search, methods=['GET', 'POST'])
        self.app.add_url_rule(rule="/search/<string:search>", view_func=self.search, methods=['GET'])
        self.app.add_url_rule(rule="/searchv2/<string:search>", view_func=self.searchv2, methods=['GET'])
        self.app.add_url_rule(rule="/exit", view_func=self.exit, methods=['GET', 'POST'])
        self.app.add_url_rule(rule="/info", view_func=self.info, methods=['GET'])

        # register default error handler
        self.app.register_error_handler(code_or_exception=404, f=self.not_found)

    def run(self):
        self._server.serve_forever()

    def not_found(self, error):
        return make_response(jsonify({'error': 'Not found'}), 404)

    def index(self):
        """Serve the main index page"""
        return send_from_directory('static', 'index.html')

    def _exit_program(self):
        time.sleep(3)
        logger.debug("shutting down")
        os._exit(0)

    def exit(self):
        """exit program"""
        thread = Thread(target=self._exit_program)
        thread.start()

        return "shutdown hereafter"

    def info(self):
        return self.appinfo.get()
        
    def audio_file(self, path):
        """Serve files from the audio directory"""
        logger.debug("serving file: %s" % path)
        # TODO quickfix "../", won't work properly for other paths, rendering config audio_path unusable
        return send_from_directory("../" + self.audio_path, path)
        
    def delete_by_search(self, search):
        """insert a search string (one that was already given) an delete the resource backed by it."""
        quoted_search = quote(search)

        name_of_file_or_false = self.cache.remove_from_cache_by_search(quoted_search)
        if (name_of_file_or_false):
            os.remove(os.path.join(self.audio_path, name_of_file_or_false))
            return "ok"
        
        return make_response(jsonify({'error': 'Not found'}), 404)

    def search(self, search):
        """search the string, return the url to the mp3."""
        # search_query_extended_for youtube_dl
        quoted_search = quote(search)
        logger.debug("searching for file: %s" % quoted_search)
        
        result = None
        cache_result = self.cache.retrieve_from_cache(quoted_search)
        if (cache_result is not None):
            result = cache_result
            logger.debug("found in cache")
        else:
            logger.debug("not found in cache")
            # download via youtube-dl
            result = self.downloader.download_to_and_return_path(search)
            if (len(result) < 1):
                return make_response(jsonify({'error': 'internal error'}), 500)
            
            # put into cache
            self.cache.put_to_cache(quoted_search, result)
            
        # put together the result URL
        return self.AUDIO_DIR + result

    def searchv2(self, search):
        """search the string, return dict containing at least 'filename', 'path', and 'by'. Where path contains the path to the file."""
        # search_query_extended_for youtube_dl
        quoted_search = quote(search)
        logger.debug("searchingv2 for file: %s" % quoted_search)
        
        result = {}
        resulting_cache_filename = self.cache.retrieve_from_cache(quoted_search)
        if (resulting_cache_filename is not None):
            logger.debug("searchingv2 found in cache")
            result['filename'] = resulting_cache_filename
            result['by'] = "cache"
            
        else:
            logger.debug("searchingv2 not found in cache")
            # download via youtube-dl
            info = self.downloader.download_to_and_return_info(search)
            if (len(info) < 1):
                return make_response(jsonify({'error': 'internal error'}), 500)
            result = info
            result['by'] = "download"

            # put into cache
            self.cache.put_to_cache(quoted_search, result['filename'])
        
        # put together the result URL
        result['path'] = self.AUDIO_DIR + result['filename']
        return result
        