import unittest
from unittest.mock import MagicMock, patch
from youtube_audio_provider.downloader import Downloader


class TestDownloadContext(unittest.TestCase):
    def setUp(self):
        self.mock_ydl = MagicMock()
        self.mock_ydl.extract_info.return_value = {
            'entries': [{'id': 'test_id', 'title': 'Test Title', 'channel': 'Test Channel', 'artist': 'Test Artist'}]
        }
        self.mock_ydl.download = MagicMock()
        self.ffmpeg_location = "/mock/ffmpeg"
        self.destination_path = "/mock/destination"
        self.search_string = "test search"

    @patch("youtube_audio_provider.downloader.yt_dlp.YoutubeDL", return_value=MagicMock())
    def test_get_id(self, mock_ytdl_class):
        mock_ytdl_class.return_value = self.mock_ydl
        context = Downloader.DownloadContext(self.ffmpeg_location, self.destination_path, self.search_string)
        video_id = context.get_id()

        self.assertEqual(video_id, "test_id")
        self.assertEqual(context.info['title'], "Test Title")
        self.assertEqual(context.info['channel'], "Test Channel")
        self.assertEqual(context.info['artist'], "Test Artist")
        self.mock_ydl.extract_info.assert_called_once_with(f"ytsearch:{self.search_string}", download=False)

    @patch("youtube_audio_provider.downloader.yt_dlp.YoutubeDL", return_value=MagicMock())
    def test_download(self, mock_ytdl_class):
        mock_ytdl_class.return_value = self.mock_ydl
        context = Downloader.DownloadContext(self.ffmpeg_location, self.destination_path, self.search_string)
        context.info = {'id': 'test_id'}
        context.final_filepath = "/mock/destination/test_file.mp3"

        result = context.download()

        self.mock_ydl.download.assert_called_once_with(["https://www.youtube.com/watch?v=test_id"])
        self.assertEqual(result['filename'], "test_file.mp3")

    @patch("youtube_audio_provider.downloader.yt_dlp.YoutubeDL", return_value=MagicMock())
    def test_get_info(self, mock_ytdl_class):
        mock_ytdl_class.return_value = self.mock_ydl
        context = Downloader.DownloadContext(self.ffmpeg_location, self.destination_path, self.search_string)
        context.info = {'id': 'test_id', 'title': 'Test Title'}

        info = context.get_info()

        self.assertEqual(info['id'], 'test_id')
        self.assertEqual(info['title'], 'Test Title')


class TestDownloader(unittest.TestCase):
    def setUp(self):
        self.mock_config = {'ffmpeg_location': '/mock/ffmpeg', 'audio_path': '/mock/audio'}
        self.mock_info = MagicMock()
        self.downloader = Downloader(self.mock_config, self.mock_info)
        self.downloader.downloader = MagicMock()

    def test_download_to_and_return_path(self):
        self.downloader.downloader.download.return_value = {'filename': 'test_file.mp3'}
        result = self.downloader.download_to_and_return_path("test search")

        self.downloader.downloader.download.assert_called_once_with("test search", "/mock/audio")
        self.assertEqual(result, "test_file.mp3")

    def test_download_to_and_return_info(self):
        self.downloader.downloader.download.return_value = {
            'id': 'test_id',
            'filename': 'test_file.mp3',
            'title': 'Test Title'
        }
        result = self.downloader.download_to_and_return_info("test search")

        self.downloader.downloader.download.assert_called_once_with("test search", "/mock/audio")
        self.assertEqual(result['id'], 'test_id')
        self.assertEqual(result['filename'], 'test_file.mp3')
        self.assertEqual(result['title'], 'Test Title')
