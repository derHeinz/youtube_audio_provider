import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from youtube_audio_provider.cache_db import Cache, Entry, SearchPhrase


class TestCache(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_exporter = MagicMock()
        self.mock_appinfo = MagicMock()
        self.cache = Cache(self.mock_exporter, self.mock_appinfo, "/mock/audio/files")

    def _mock_session(self, mock_session_class):
        mock_session = MagicMock(spec=Session)
        mock_session_class.return_value.__enter__.return_value = mock_session
        return mock_session

    @patch("youtube_audio_provider.cache_db.Session")
    def test_put_to_cache_creates_new_entry(self, mock_session_class):
        # Arrange
        mock_session = self._mock_session(mock_session_class)
        mock_session.scalars.return_value.first.return_value = None  # Simulate no existing entry

        quoted_search = "Test Phrase"
        kwargs = {"id": "1", "filename": "test.mp3", "title": "Test Title", "artist": "Test Artist"}

        # Act
        self.cache.put_to_cache(quoted_search, **kwargs)

        # Assert
        mock_session.add.assert_called()  # Ensure new entry and phrase are added
        mock_session.commit.assert_called_once()  # Ensure changes are committed
        self.mock_appinfo.register.assert_called()  # Ensure cache size is updated

    @patch("youtube_audio_provider.cache_db.Session")
    def test_put_to_cache_updates_existing_entry(self, mock_session_class):
        # Arrange
        mock_session = self._mock_session(mock_session_class)
        existing_entry = Entry(id="1", filename="test.mp3", title="Old Title", artist="Old Artist")
        mock_session.scalars.return_value.first.return_value = existing_entry  # Simulate existing entry

        quoted_search = "Updated Phrase"
        kwargs = {"id": "1", "filename": "test.mp3", "title": "New Title", "artist": "New Artist"}

        # Act
        self.cache.put_to_cache(quoted_search, **kwargs)

        # Assert
        mock_session.add.assert_called()  # Ensure new phrase is added
        mock_session.commit.assert_called_once()  # Ensure changes are committed
        self.mock_appinfo.register.assert_called()  # Ensure cache size is updated

    @patch("youtube_audio_provider.cache_db.Session")
    def test_put_to_cache_simplifies_search_phrase(self, mock_session_class):
        # Arrange
        mock_session = self._mock_session(mock_session_class)
        mock_session.scalars.return_value.first.return_value = None  # Simulate no existing entry

        quoted_search = "CaseInsensitive Phrase"
        kwargs = {"id": "1", "filename": "test.mp3", "title": "Test Title", "artist": "Test Artist"}

        # Act
        self.cache.put_to_cache(quoted_search, **kwargs)

        # Assert
        simplified_phrase = quoted_search.casefold()
        self.assertEqual(mock_session.add.call_args[0][0].phrase, simplified_phrase)  # Ensure phrase is simplified

    @patch("youtube_audio_provider.cache_db.Session")
    def test_add_searchphrase_to_id_adds_phrase(self, mock_session_class):
        # Arrange
        mock_session = self._mock_session(mock_session_class)
        existing_entry = Entry(id="1", filename="test.mp3", title="Test Title", artist="Test Artist")
        mock_session.scalars.return_value.first.return_value = existing_entry  # Simulate existing entry

        id = "1"
        quoted_search = "New Phrase"

        # Act
        self.cache.add_searchphrase_to_id(id, quoted_search)

        # Assert
        mock_session.add.assert_called()  # Ensure new phrase is added
        mock_session.commit.assert_called_once()  # Ensure changes are committed

    @patch("youtube_audio_provider.cache_db.Session")
    def test_add_searchphrase_to_id_raises_error_for_invalid_id(self, mock_session_class):
        # Arrange
        mock_session = self._mock_session(mock_session_class)
        mock_session.scalars.return_value.first.return_value = None  # Simulate no entry found

        id = "invalid_id"
        quoted_search = "New Phrase"

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            self.cache.add_searchphrase_to_id(id, quoted_search)
        self.assertIn("entry with id invalid_id cold not be found", str(context.exception))

    @patch("youtube_audio_provider.cache_db.Session")
    def test_remove_from_cache_by_search_removes_entry(self, mock_session_class):
        # Arrange
        mock_session = self._mock_session(mock_session_class)
        existing_entry = Entry(id="1", filename="test.mp3", title="Test Title", artist="Test Artist")
        mock_session.scalars.return_value.first.return_value = existing_entry  # Simulate existing entry

        quoted_search = "Test Phrase"

        # Act
        result = self.cache.remove_from_cache_by_search(quoted_search)

        # Assert
        mock_session.delete.assert_called_with(existing_entry)  # Ensure entry is deleted
        mock_session.commit.assert_called_once()  # Ensure changes are committed
        self.assertEqual(result, "test.mp3")  # Ensure filename is returned

    @patch("youtube_audio_provider.cache_db.Session")
    def test_remove_from_cache_by_search_returns_false_if_not_found(self, mock_session_class):
        # Arrange
        mock_session = self._mock_session(mock_session_class)
        mock_session.scalars.return_value.first.return_value = None  # Simulate no entry found

        quoted_search = "Nonexistent Phrase"

        # Act
        result = self.cache.remove_from_cache_by_search(quoted_search)

        # Assert
        self.assertFalse(result)  # Ensure False is returned

    @patch("youtube_audio_provider.cache_db.Session")
    def test_retrieve_by_search_returns_entry_if_file_exists(self, mock_session_class):
        # Arrange
        mock_session = self._mock_session(mock_session_class)
        existing_entry = Entry(id="1", filename="test.mp3", title="Test Title", artist="Test Artist")
        mock_session.scalars.return_value.first.return_value = existing_entry  # Simulate existing entry
        self.cache._check_file_exists = MagicMock(return_value=True)  # Simulate file exists

        quoted_search = "Test Phrase"

        # Act
        result = self.cache.retrieve_by_search(quoted_search)

        # Assert
        self.assertEqual(result, {"title": "Test Title", "artist": "Test Artist", "filename": "test.mp3"})

    @patch("youtube_audio_provider.cache_db.Session")
    def test_retrieve_by_search_returns_none_if_file_not_exists(self, mock_session_class):
        # Arrange
        mock_session = self._mock_session(mock_session_class)
        existing_entry = Entry(id="1", filename="test.mp3", title="Test Title", artist="Test Artist")
        mock_session.scalars.return_value.first.return_value = existing_entry  # Simulate existing entry
        self.cache._check_file_exists = MagicMock(return_value=False)  # Simulate file does not exist

        quoted_search = "Test Phrase"

        # Act
        result = self.cache.retrieve_by_search(quoted_search)

        # Assert
        self.assertIsNone(result)

    @patch("youtube_audio_provider.cache_db.Session")
    def test_retrieve_by_id_returns_entry_if_file_exists(self, mock_session_class):
        # Arrange
        mock_session = self._mock_session(mock_session_class)
        existing_entry = Entry(id="1", filename="test.mp3", title="Test Title", artist="Test Artist")
        mock_session.scalars.return_value.first.return_value = existing_entry  # Simulate existing entry
        self.cache._check_file_exists = MagicMock(return_value=True)  # Simulate file exists

        id = "1"

        # Act
        result = self.cache.retrieve_by_id(id)

        # Assert
        self.assertEqual(result, {"title": "Test Title", "artist": "Test Artist", "filename": "test.mp3"})

    @patch("youtube_audio_provider.cache_db.Session")
    def test_fulltext_search_returns_matching_results(self, mock_session_class):
        # Arrange
        mock_session = self._mock_session(mock_session_class)
        mock_session.execute.return_value.unique.return_value.all.return_value = [
            (Entry(id="1", filename="test.mp3", title="Test Title", artist="Test Artist"), 
             SearchPhrase(phrase="Test Phrase"))
        ]  # Simulate matching results

        quoted_search = "Test"

        # Act
        result = self.cache.fulltext_search(quoted_search)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].filename, "test.mp3")
        self.assertEqual(result[0].title, "Test Title")
        self.assertEqual(result[0].artist, "Test Artist")
