#!/usr/bin/python3
# -*- coding: utf

import unittest
from unittest.mock import MagicMock, patch
import json

from youtube_audio_provider.appinfo import AppInfo
from youtube_audio_provider.downloader import Downloader


class TestDownloader(unittest.TestCase):

    FFMPEG_LOCATION = 'bla'

    def _create_testee(self) -> Downloader:
        config = {
            'ffmpeg_location': self.FFMPEG_LOCATION,
            'audio_path': 'audio'
        }
        return Downloader(config, AppInfo())
    
    @patch("youtube_audio_provider.downloader.subprocess.run")
    @patch("youtube_audio_provider.downloader.subprocess.check_output")
    def test_download_youtubedl(self, check_output_mock, run_mock):
        # process calls subprocess 4 times:
        # 1. subprocess.check_output to check for downloader yt-dl
        # 2. subprocess.check_output to check for downoader youtube-dl
        # 3. subprocess.run to retrieve youtube id
        # 4. subprocess.run to download the file

        magic_dir = "audio"
        test_search_string = "foobar"
        search_result = {
            "id": "0815",
            "fulltitle": "foo-bar-foo",
            "title": "foo-bar",
            "channel": "b-chan"
        }

        # define order of execution
        check_output_mock.side_effect = [Exception('bla'), bytes('yes', 'utf8')]

        find_youtube_info_mock = MagicMock()
        find_youtube_info_mock.stdout = json.dumps(search_result)

        download_youtube_id_mock = MagicMock()
        download_youtube_id_mock.stderr = ''
        download_youtube_id_mock.stdout = '[ffmpeg] Destination: ' + magic_dir + '/testfile.mp3\n'
        run_mock.side_effect = [find_youtube_info_mock, download_youtube_id_mock]

        d = self._create_testee()
        res = d.download_to_and_return_info(test_search_string)

        # define called in order of execution
        check_output_mock.assert_any_call(['yt-dlp', '--version'])
        check_output_mock.assert_any_call(['youtube-dl', '--version'])
        run_mock.assert_any_call(['youtube-dl', 'ytsearch:' + test_search_string, '-j'],
                                 capture_output=True, encoding='utf-8')
        run_mock.assert_any_call(['youtube-dl', '-x',
                                 '--audio-format', 'mp3',
                                  '--audio-quality', '0',
                                  '--ffmpeg-location', self.FFMPEG_LOCATION,
                                  '-o', 'audio/%(title)s.%(ext)s',
                                  'https://www.youtube.com/watch?v=' + search_result['id']],
                                 capture_output=True, encoding='utf-8')

        self.assertEqual(search_result['id'], res['id'])
        self.assertEqual(search_result['title'], res['title'])
        self.assertEqual(search_result['channel'], res['channel'])
        self.assertEqual('testfile.mp3', res['filename'])

    @patch("youtube_audio_provider.downloader.subprocess.run")
    @patch("youtube_audio_provider.downloader.subprocess.check_output")
    def test_download_ytdlp(self, check_output_mock, run_mock):
        # process calls subprocess 3 times:
        # 1. subprocess.check_output to check for downloader
        # 2. subprocess.run to retrieve youtube id
        # 3. subprocess.run to download the file

        magic_dir = "audio"
        test_search_string = "asfd"
        search_result = {
            "id": "4711",
            "title": "qaqaqa",
            "channel": "a-chan"
        }

        # define order of execution
        check_output_mock.return_value = bytes('yes', 'utf8')

        find_youtube_info_mock = MagicMock()
        find_youtube_info_mock.stdout = json.dumps(search_result)

        download_youtube_id_mock = MagicMock()
        download_youtube_id_mock.stderr = ''
        download_youtube_id_mock.stdout = '[ExtractAudio] Destination: ' + magic_dir + '/testfile.mp3\n'
        run_mock.side_effect = [find_youtube_info_mock, download_youtube_id_mock]

        d = self._create_testee()
        res = d.download_to_and_return_info(test_search_string)

        # define called in order of execution
        check_output_mock.assert_called_once_with(['yt-dlp', '--version'])
        run_mock.assert_any_call(['yt-dlp', 'ytsearch:' + test_search_string, '-j'],
                                 capture_output=True, encoding='utf-8')
        run_mock.assert_any_call(['yt-dlp', '-x', '-N', ' 4',
                                 '--audio-format', 'mp3',
                                  '--audio-quality', '0',
                                  '--ffmpeg-location', self.FFMPEG_LOCATION,
                                  '-o', 'audio/%(title)s.%(ext)s',
                                  'https://www.youtube.com/watch?v=' + search_result['id']],
                                 capture_output=True, encoding='utf-8')

        self.assertEqual(search_result['id'], res['id'])
        self.assertEqual(search_result['title'], res['title'])
        self.assertEqual(search_result['channel'], res['channel'])
        self.assertEqual('testfile.mp3', res['filename'])
