import json
import youtube_dl

class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')

ydl_opts = {
    'format': 'aac',
    'logger': MyLogger(),
    'progress_hooks': [my_hook]
}

class Streamextractor(object):

    def get_stream(self, search_string):
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            yt_info = ydl.extract_info(f"ytsearch:{search_string}", download=False)
            #s = json.loads(yt_info)
            print(json.dumps(yt_info, indent=4, sort_keys=True))
            
            #print(yt_info)
            first = yt_info['entries'][0]
            return first['url']
