import os
import json
from json.decoder import JSONDecodeError
import logging
from collections import namedtuple

logger = logging.getLogger(__name__)

Item = namedtuple('Item', ['phrase', 'filename'])


class Cache(object):

    def __init__(self, audio_file_directory):
        self.cachefile = "cache.json"
        self.audio_file_directory = audio_file_directory

        self.cache = {}
        logger.debug("loading cache")
        self._load_cache()
        logger.info("loaded %d entries" % len(self.cache))

    def _load_cache_from_disk(self):
        # create empty json in case of non-existence
        if (not os.path.exists(self.cachefile)):
            with (open(self.cachefile, mode ='a', encoding='utf-8')) as data_file:
                json.dump({}, data_file)  # empty file
        
        # extract cache from persistent cache file
        with open(self.cachefile, encoding='utf-8') as data_file:
            try:
                self.cache = json.load(data_file)
            except JSONDecodeError:
                pass

    def _load_cache(self):
        self._load_cache_from_disk()

    def _check_file_exists(self, filename: str):
        path = os.path.join(self.audio_file_directory, filename)
        logger.debug(f"looking for file '{path}'")
        if (os.path.exists(path)):
            return True
        return False

    def _store_cache_to_disk(self):
        # persist into cachefile e.g. for restart
        with open(self.cachefile, 'w') as outfile:
            json.dump(self.cache, outfile)
    
    def all_items(self):
        items = []
        for key, val in self.cache.items():
            items.append(Item(phrase=key, filename=val))
        return items
