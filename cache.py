import os
import json
import uuid
from json.decoder import JSONDecodeError
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class AudioResource(db.Model):
    """SQLAlchemy resouce class"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    search = db.Column(db.String(120), index=True, unique=True)
    filename = db.Column(db.String(1000))
    stream_url = db.Column(db.String(1000))
        
    def __repr__(self):
        """Return a string representation of a resource"""
        return '<Resource (%d): %s>' % (self.id, self.search)

class AudioCache(object):

    def __init__(self, flask_app, exporter):
        self.app = flask_app
        # db stuff
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///audiocache.db'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        #self.app.config['SQLALCHEMY_ECHO'] = True

        db.init_app(self.app)
        db.create_all() # probably create tables
        
        self.exporter = exporter
        
    def _get_resource_with_id(self, id):
        return AudioResource.query.get(id)
        
    def _get_resource_with_search(self, search):
        search_p = self._search_to_persitent_format(search)
        return AudioResource.query.filter_by(search=search).first()
        
    def _get_new_id(self):
        while True:
            new_id = uuid.uuid4()
            if (self._get_resource_with_id(new_id) is None):
                return new_id
                
    def _search_to_persitent_format(self, search):
        return search.casefold()
        
    def _persist(self, id):
        # save to local db
        db.session.commit()
        
        # save into exporter
        all = AudioResource.query.all()
        self.exporter.export(all)

    def is_known(self, id):
        if (self._get_resource_with_id(id) != None):
            return True
        return False
        
    def retrieve(self, id):
        ar = self._get_resource_with_id(id)
        if ar is None:
            return None
        
        if (ar.filename):
            return ar.filename
        else:
            return ar.stream_url
        
    def retrieve_id_by_search(self, search):
        ar = self._get_resource_with_search(search)
        if (ar == None):
            return None
            
        return ar.id
        
    def is_stream(self, id):
        ar = self._get_resource_with_id(id)
        if (ar.filename):
            return False
        else:
            return True
        
    def add_filename(self, id, filename):
        ar = self._get_resource_with_id(id)
        if (ar == None):
            raise ValueError("it is wrong to add a filename to a non-existing entry.")
            
        ar.filename = filename
        self._persist(ar.id)
        
    def put_new_stream(self, search, stream_url):
        search_p = self._search_to_persitent_format(search)
        
        ar = self._get_resource_with_search(search_p)
        if (ar != None):
            raise ValueError("it is wrong to put another value for the same search query.")
    
        ar = AudioResource()
        ar.search = search_p
        ar.stream_url = stream_url
        
        db.session.add(ar)
        self._persist(ar.id)
        
        return ar.id


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
        