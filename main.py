#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import json
import os
import logging

from webserver import Webserver
from downloader import Downloader
from cache_html_exporter import CacheHTMLExporter

logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.info("logger configured")

def load_config(): 
    # load configuration from config file
    with open('config.json') as data_file:    
        return json.load(data_file)

def store_pid_file(pidfilename):
    pid = str(os.getpid())
    f = open(pidfilename, 'w')
    f.write(pid)
    f.close()

def main():

    store_pid_file("pidfile.pid")
    config_data = load_config()
    setup_logging()

    exporter = CacheHTMLExporter(config_data['cache_export_config'])
    dl = Downloader(config_data['ffmpeg_location'])
    ws = Webserver(config_data['webserver_port'], dl, exporter)
    
    # incase this is run as deamon
    # ws.setDaemon(True)
    
    try:
        ws.start()
    except KeyboardInterrupt:
        print("Exiting\n")
        sys.exit(0)

if __name__ == '__main__':
    main()
