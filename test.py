# from downloader import Downloader
import subprocess
import sys

enc = sys.getdefaultencoding()
print(enc)
ffmpeg_loc = "D:\\HeinzDaten\\Projekte\\Python\\ffmpeg-20200216-8578433-win64-static\\bin"

# d = Downloader(ffmpeg_loc)

def cmd_line(search_string):
    params = ['youtube-dl',
        'ytsearch25:' + search_string,
        '-x', 
        '--audio-format', 'mp3', 
        '--audio-quality', '0', 
        '--ffmpeg-location', ffmpeg_loc]
    result = subprocess.run(params, capture_output=True, encoding='cp1252')
    
    print("stderr")
    print(result.stderr)
    print("stdout")
    print(result.stdout)
    return str(result.stdout).rstrip("\n")
    
    
cmd_line("Benjamin Blümchen Krankenhaus")

#d.download_to("take that never forget", "D:\\HeinzDaten\\Projekte\\Python\\youtube_audio_provider\\audio")
#id = d.find_youtube_id('kinderlied igel')
#print(id)

#id = d.find_youtube_id('kinderlied')
#print(id)
#d.download_youtube_id_to(id, 'D:\\HeinzDaten\\Projekte\\Python\\youtube_audio_provider\\audio')


