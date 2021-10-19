#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import json
import os

from cache import Cache
from webserver import Webserver
from downloader import Downloader
from streamextractor import Streamextractor
from cache_html_exporter import CacheHTMLExporter

def load_config(): 
    # load configuration from config file
    with open('config.json') as data_file:    
        return json.load(data_file)

def main():

    config_data = load_config()

    exporter = CacheHTMLExporter(config_data['cache_export_config'])
    cache = Cache(exporter)
    
    dl = Downloader(config_data['ffmpeg_location'])
    ext = Streamextractor()
    ws = Webserver(config_data['webserver_port'], dl, ext, cache)
    
    # incase this is run as deamon
    # ws.setDaemon(True)
    
    try:
        ws.start()
    except KeyboardInterrupt:
        print("Exiting\n")
        sys.exit(0)

if __name__ == '__main__':
    main()
