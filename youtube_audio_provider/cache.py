#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import json
from json.decoder import JSONDecodeError
import logging
from collections import namedtuple
from typing import List

from youtube_audio_provider.appinfo import AppInfo
from youtube_audio_provider.finder import Finder

logger = logging.getLogger(__name__)

Item = namedtuple('Item', ['phrase', 'filename'])


class Cache(object):

    def __init__(self, exporter, info: AppInfo, audio_file_directory):
        self.cachefile = "cache.json"
        self.appinfo = info
        self.audio_file_directory = audio_file_directory

        self.cache = {}
        self.index: Finder = None
        logger.debug("loading cache")
        self._load_cache()
        logger.info("loaded %d entries" % len(self.cache))

        self.exporter = exporter

    def _load_cache_from_disk(self):
        # create empty json in case of non-existence
        if (not os.path.exists(self.cachefile)):
            with (open(self.cachefile, 'a')) as data_file:
                json.dump({'dummy': 'dummy'}, data_file)
        
        # extract cache from persistent cache file
        with open(self.cachefile) as data_file:
            try:
                self.cache = json.load(data_file)
            except JSONDecodeError:
                pass

    def _load_cache(self):
        self._load_cache_from_disk()
        self.index = Finder(self.cache)
        # report
        self.appinfo.register('cache_size', len(self.cache))

    def _check_file_exists(self, filename: str):
        path = os.path.join(self.audio_file_directory, filename)
        logger.debug(f"looking for file '{path}'")
        if (os.path.exists(path)):
            return True
        return False

    def retrieve_from_cache(self, quoted_search: str):
        ''' get value from cache,
        checks whether file is available, otherwise invalidates cache '''

        # assert cache is loaded.
        simplified_string = quoted_search.casefold()

        if (self.cache is not None and simplified_string in self.cache):
            logger.debug(f"cache hit for '{simplified_string}'")
            cached_filename = self.cache[simplified_string]
            # check file exists:
            if self._check_file_exists(cached_filename):
                return cached_filename
        return None

    def _store_cache_to_disk(self):
        # persist into cachefile e.g. for restart
        with open(self.cachefile, 'w') as outfile:
            json.dump(self.cache, outfile)

    def store_cache(self):
        self._store_cache_to_disk()
        # update index:
        self.index = Finder(self.cache)
        # export
        self.exporter.export(self.cache)
        # report
        self.appinfo.register('cache_size', len(self.cache))

    def put_to_cache(self, quoted_search: str, filename: str):
        # put into cache the quoted_search string together with the filename

        # assert cache is loaded and no cache hit
        simplified_string = quoted_search.casefold()

        # put value to cache
        self.cache[simplified_string] = filename
        logger.debug(f"putting into cache '{simplified_string}'")

        self.store_cache()

    def remove_from_cache_by_search(self, quoted_search):
        search_result = self.retrieve_from_cache(quoted_search)

        if (search_result is not None):
            # remove all occurencs of search_result in the cache
            self.cache = {key: val for key, val in
                          self.cache.items() if val != search_result}
            self.store_cache()
            return search_result

        return False

    def fulltext_search(self, quoted_search: str):
        simplified_string = quoted_search.casefold()

        search_result = self.index.find(simplified_string, exact=False)
        # i need value to display and key to send to openhab
        unique_values = set()
        result_list: List[Item] = []
        for hit in search_result:
            key = hit[0]
            value = hit[1]
            if value not in unique_values:
                unique_values.add(value)
                result_list.append(Item(key, value))

        return result_list
