# A simple yoututbe search-downloader and MP3 webserver.

It is a webserver that hosts mp3 files from a static directory. These mp3s can be played by DLNA players.

You can make a request to the webserver that invokes a youtube search. On request the first search-hit is downloaded as audio file and transfered into mp3. This mp3 in is than put into the static directory and beeing served as a static file.

For subsequent searches with the same searchterm the local file is immediately served without a youtube search beeing invoked.

Needs:
- certain python modules (see requirement.txt)
- Youtube Downloader ([youtube-dl](https://github.com/ytdl-org/youtube-dl) or [yt-dlp](https://github.com/yt-dlp/yt-dlp)) locally installed
- MP3 converter ([FFMPEG](https://www.ffmpeg.org/))
