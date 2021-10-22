#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import json
import os
from threading import Thread
from flask import Flask
from werkzeug.serving import make_server

from cache import AudioCache
from webserver import Webserver
from downloader import Downloader
from streamextractor import Streamextractor
from cache_html_exporter import CacheHTMLExporter

def load_config(): 
    # load configuration from config file
    with open('config.json') as data_file:    
        return json.load(data_file)

def create_flask(port):
    # create Flask
    app = Flask(__name__)
    app.config['port'] = port
    app.config['app_name'] = "Youtube Audio Provider"
    #app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16mb is enough for posts
        
    app.app_context().push()
    return app
    

def main():

    config_data = load_config()
    
    flask_app = create_flask(config_data['webserver_port'])

    exporter = CacheHTMLExporter(config_data['cache_export_config'])
    cache = AudioCache(flask_app, exporter)
    
    dl = Downloader(config_data['ffmpeg_location'])
    ext = Streamextractor()
    ws = Webserver(flask_app, dl, ext, cache)
    
    # incase this is run as deamon
    # ws.setDaemon(True)
    
    server = make_server(host='0.0.0.0', port=flask_app.config['port'], app=flask_app, threaded=True)
    print("Starting %s on port %d" % (flask_app.config['app_name'], flask_app.config['port']))
    
    try:
        server_thread = Thread(target=server.serve_forever(), daemon=True)
        server_thread.start()
    except KeyboardInterrupt:
        print("Exiting\n")
        sys.exit(0)

if __name__ == '__main__':
    main()
