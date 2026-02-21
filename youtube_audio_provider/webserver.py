import os
import time
from threading import Thread
from flask import Flask, send_from_directory, make_response, render_template
from flask.json import jsonify
from werkzeug.serving import make_server
from urllib.parse import quote
import logging

from youtube_audio_provider.cache_db import Cache, Item
from youtube_audio_provider.downloader import Downloader
from youtube_audio_provider.appinfo import AppInfo

logger = logging.getLogger(__name__)


class Webserver(Thread):

    AUDIO_DIR_NAME = 'audio'
    AUDIO_DIR = '/' + AUDIO_DIR_NAME + '/'

    def __init__(self, config, downloader: Downloader,
                 cache: Cache, info: AppInfo):
        """Create a new instance of the flask app"""
        super(Webserver, self).__init__()

        self.audio_path = config.get('audio_path', 'audio')

        cache_export_config = config.get('cache_export_config', None)
        self.audio_search_callurl = cache_export_config.get('callurl', None)
        self.audio_search_prefix = cache_export_config.get('prefix', None)

        # TODO calculate audio_path as seen by flask with it's root_path: self.app.root_path
        info.register('audio_directory', os.path.abspath(self.audio_path))
        self.downloader = downloader
        self.appinfo = info
        self.cache = cache

        self.app = Flask(__name__)
        self.app.config['port'] = config['webserver_port']
        self.app.config['app_name'] = "Youtube Audio Provider"
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16mb is enough
        self.app.config['webserver_cors_allow'] = config.get('webserver_cors_allow', False)

        self.app.app_context().push()
        self._server = make_server(host='0.0.0.0', port=self.app.config['port'], app=self.app, threaded=True)
        logger.info("Starting %s on port %d\nPress CTRL-C to exit" % (self.app.config['app_name'], self.app.config['port']))

        # register some endpoints
        self.app.add_url_rule(rule="/", view_func=self.index, methods=['GET'])
        self.app.add_url_rule(rule="/audio_search", view_func=self.audio_search, methods=['GET'])
        self.app.add_url_rule(rule="/audio/<path:path>", view_func=self.audio_file, methods=['GET'])
        # allow GET, this is for simple browser deletion
        self.app.add_url_rule(rule="/delete_by_search/<string:search>",
                              view_func=self.delete_by_search, methods=['GET', 'POST'])
        self.app.add_url_rule(rule="/searchv2/<string:search>", view_func=self.searchv2, methods=['GET'])
        self.app.add_url_rule(rule="/find_fulltext/<string:search>", view_func=self.find_fulltext, methods=['GET'])
        self.app.add_url_rule(rule="/exit", view_func=self.exit, methods=['GET', 'POST'])
        self.app.add_url_rule(rule="/info", view_func=self.info, methods=['GET'])

        # register default error handler
        self.app.register_error_handler(code_or_exception=404, f=self.not_found)

    def run(self):
        self._server.serve_forever()

    def _add_cors_to_response(self, response):
        logger.debug('adding cors header')
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    def _make_response_and_add_cors(self, something, status_code=200):
        response = make_response(something, status_code)
        if (self.app.config['webserver_cors_allow']):
            self._add_cors_to_response(response)
        return response

    def not_found(self, error):
        return self._make_response_and_add_cors(jsonify({'error': 'Not found'}), 404)

    def index(self):
        """Serve the main index page"""
        return self._add_cors_to_response(send_from_directory('static', 'index.html'))
    
    def audio_search(self):
        """Serve the audio_search page"""
        config = {
            "audio_search_callurl": self.audio_search_callurl,
            "audio_search_prefix": self.audio_search_prefix
        }
        return self._make_response_and_add_cors(render_template('audio_search.html', **config))

    def _exit_program(self):
        time.sleep(3)
        logger.debug("shutting down")
        os._exit(0)

    def exit(self):
        """exit program"""
        thread = Thread(target=self._exit_program)
        thread.start()

        return self._make_response_and_add_cors("shutdown hereafter")

    def info(self):
        return self.appinfo.get()

    def audio_file(self, path):
        """Serve files from the audio directory"""
        logger.debug("serving file: %s" % path)
        # TODO quickfix "../", won't work properly for other paths, rendering config audio_path unusable
        return self._add_cors_to_response(send_from_directory("../" + self.audio_path, path))

    def delete_by_search(self, search):
        """insert a search string (one that was already given) an delete the resource backed by it."""
        quoted_search = quote(search)

        name_of_file_or_false = self.cache.remove_from_cache_by_search(quoted_search)
        if (name_of_file_or_false):
            logger.debug(f"attempting to delete file {name_of_file_or_false}")
            os.remove(os.path.join(self.audio_path, name_of_file_or_false))
            return "ok"

        return self._make_response_and_add_cors(jsonify({'error': 'Not found'}), 404)

    def searchv2(self, search):
        """search the string, return dict containing at least 'filename', 'path', and 'by'.
        Where path contains the path to the file."""
        # search_query_extended_for youtube_dl
        quoted_search = quote(search)
        logger.debug("searchingv2 for file: %s" % quoted_search)

        result = self.cache.retrieve_by_search(quoted_search)
        if (result is not None):
            logger.debug("searchingv2 found phrase in cache")
            result['by'] = "cache"

        else:
            logger.debug("searchingv2 not found in cache")
            # download via youtube-dl
            # TODO unclearness with quoted and unquoted search
            with self.downloader.create_download_context(search) as dl_ctx:
                id = dl_ctx.get_id()
                result = self.cache.retrieve_by_id(id)
                if (result is not None):
                    logger.debug("searchingv2 found id for phrase in cache")
                    self.cache.add_searchphrase_to_id(id, quoted_search)
                    result['by'] = "cached id"

                else:
                    result = dl_ctx.download()
                    if (len(result) < 1):
                        return self._make_response_and_add_cors(jsonify({'error': 'internal error'}), 500)
                    self.cache.put_to_cache(quoted_search, **result)
                    result['by'] = "download"

        # put together the result URL
        result['path'] = self.AUDIO_DIR + result['filename']
        return self._make_response_and_add_cors(result)

    def find_fulltext(self, search):
        quoted_search = quote(search)
        results = []
        search_result = self.cache.fulltext_search(quoted_search)
        item: Item
        for item in search_result:
            result = {}
            result['filename'] = item.filename
            result['artist'] = item.artist
            result['title'] = item.title
            result['by'] = "cache"
            results.append(result)

        return self._make_response_and_add_cors(results)
