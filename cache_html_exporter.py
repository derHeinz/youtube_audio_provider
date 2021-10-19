import os
import datetime
import codecs
from itertools import groupby
from urllib.parse import unquote
import json
from json.decoder import JSONDecodeError
from string import Template

class CacheHTMLExporter(object):

    def __init__(self, config):
        self.cachefile = os.path.join(os.path.dirname(__file__), "cache.json")
        self.template = config.get("template", "sample.html")
        self.filename = config.get("file", "voice_cache.html")
        self.callurl = config.get("callurl", "http://localhost:80")
        self.prefix = config.get("prefix", "")
        
    def one_row_with_several_items(self, head, texts):
        text = "\n".join(map(lambda t: '<div class="lower">' + t + "</div>", texts))
        return f'''
        <li onclick='post_voicecommand(this)'>
            <h3>{head}</h3>
            {text}
        </li>
        '''
    
    def _load_cache(self):
        # extract cache from persistent cache file
        with open(self.cachefile, mode='r', encoding="utf-8") as data_file:
            try:
                return json.load(data_file)
            except JSONDecodeError:
                pass
     
    def _load_template(self):
        with open(self.template) as template_file:    
            data = template_file.read()
            return data
            
    def export(self):
        data = self._load_cache()
        content_lines = []
        
        inv_map = {}
        if data and data.items():
            for key, val in data.items():
                quoted_key = unquote(key)
                inv_map[val] = inv_map.get(val, []) + [quoted_key]

        content_lines = []      
        
        for a in inv_map:
            quoted_a = unquote(a)
            content_lines.append(self.one_row_with_several_items(quoted_a,inv_map[a]))
        
        content_text = "\n".join(sorted(content_lines))
        self.write_template_outfile(content_text)
        
    def write_template_outfile(self, content_text):
        now = datetime.datetime.now()
        current_time = now.strftime("%d.%m.%Y %H:%M")
        
        templ = Template(self._load_template())
        file_text = templ.safe_substitute(content=content_text, updated=current_time, callurl=self.callurl, prefix=self.prefix)
        with codecs.open(self.filename, 'w', "utf-8") as outfile:
            outfile.write(file_text)
