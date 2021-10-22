#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import json
import os

from webserver import Webserver
from downloader import Downloader
from cache_html_exporter import CacheHTMLExporter

def load_config(): 
    # load configuration from config file
    with open('config.json') as data_file:    
        return json.load(data_file)

def main():

    config_data = load_config()

    exporter = CacheHTMLExporter(config_data['cache_export_config'])
    dl = Downloader(config_data['ffmpeg_location'])
    ws = Webserver(config_data['webserver_port'], dl, exporter)
    
    # incase this is run as deamon
    # ws.setDaemon(True)
    
    try:
        print("Starting Youtube Audio Provider\nPress CTRL-C to exit")
        ws.start()
    except KeyboardInterrupt:
        print("Exiting\n")
        sys.exit(0)

if __name__ == '__main__':
    main()
