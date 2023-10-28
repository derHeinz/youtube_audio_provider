#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import json
import os
import logging

from youtube_audio_provider.webserver import Webserver
from youtube_audio_provider.downloader import Downloader
from youtube_audio_provider.exporter.cache_html_exporter import CacheHTMLExporter
from youtube_audio_provider.appinfo import AppInfo

logger = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.DEBUG,
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
    setup_logging()
    logger.debug(f'PID: {os.getpid()}')
    config_data = load_config()

    info = AppInfo()
    info.register('config', config_data) # put full config into info
    exporter = CacheHTMLExporter(config_data)
    dl = Downloader(config_data, info)
    ws = Webserver(config_data, dl, exporter, info)
    
    # incase this is run as deamon
    # ws.setDaemon(True)
    
    try:
        ws.start()
    except KeyboardInterrupt:
        print("Exiting\n")
        sys.exit(0)

if __name__ == '__main__':
    main()
