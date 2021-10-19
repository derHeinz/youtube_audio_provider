import os
import json
from json.decoder import JSONDecodeError

class Cache(object):

    def __init__(self, exporter):
        self.cachefile = os.path.join(os.path.dirname(__file__), "cache.json")
        self.cache = {}
        self._load_cache()
        
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
            print("cache hit for '{}'".format(simplified_string))
            cached_filename = self.cache[simplified_string]
            # check file exists:
            full_path = os.path.join(self.audio_file_directory, cached_filename)
            print("looking for file '{}'".format(full_path))
            if (os.path.exists(full_path)):
                return cached_filename
        return None

    def put_to_cache(self, quoted_search, filename): 
        # put into cache the quoted_search string together with the filename
        
        # assert cache is loaded and no cache hit
        simplified_string = quoted_search.casefold()
        
        # put value to cache
        self.cache[simplified_string] = filename
        print("putting into cache '{}'".format(simplified_string))
        
        # persist into cachefile for restart
        with open(self.cachefile, 'w') as outfile:
            json.dump(self.cache, outfile)
            
        self.exporter.export()
        