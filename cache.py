#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import json
from json.decoder import JSONDecodeError
import logging

logger = logging.getLogger(__name__)

class Cache(object):

    def __init__(self, exporter, audio_file_directory):
        self.cachefile = os.path.join(os.path.dirname(__file__), "cache.json")
        self.cache = {}
        logger.debug("loading cache")
        self._load_cache()
        logger.info("loaded %d entries" % len(self.cache))
        
        self.audio_file_directory = audio_file_directory

        self.exporter = exporter
        self.exporter.export()

    def _load_cache(self):
        # extract cache from persistent cache file
        with open(self.cachefile) as data_file:
            try:
                self.cache = json.load(data_file)
            except JSONDecodeError:
                pass

    def retrieve_from_cache(self, quoted_search):
        # gets value from cache, checks whether file is available, otherwise invalidates cache
        
        # assert cache is loaded.
        simplified_string = quoted_search.casefold()

        if (self.cache != None and simplified_string in self.cache):
            logger.debug("cache hit for '{}'".format(simplified_string))
            cached_filename = self.cache[simplified_string]
            # check file exists:
            full_path = os.path.join(self.audio_file_directory, cached_filename)
            logger.debug("looking for file '{}'".format(full_path))
            if (os.path.exists(full_path)):
                return cached_filename
        return None

    def store_cache(self):
        # persist into cachefile for restart
        with open(self.cachefile, 'w') as outfile:
            json.dump(self.cache, outfile)

    def put_to_cache(self, quoted_search, filename): 
        # put into cache the quoted_search string together with the filename
        
        # assert cache is loaded and no cache hit
        simplified_string = quoted_search.casefold()
        
        # put value to cache
        self.cache[simplified_string] = filename
        logger.debug("putting into cache '{}'".format(simplified_string))
        
        self.store_cache()
            
        self.exporter.export()

    def remove_from_cache_by_search(self, quoted_search):
        search_result = self.retrieve_from_cache(quoted_search)

        if (search_result is not None):
            # remove all occurencs of search_result in the cache
            self.cache = {key:val for key, val in self.cache.items() if val != search_result}
            self.store_cache()
            return search_result
        
        return False