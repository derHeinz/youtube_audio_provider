
import unittest
from cache import AudioCache

class TestAudioCache(unittest.TestCase):
    
    def _testee(sef):
        return AudioCache()
        
    def test_put_retrieve(self):
        cache = self._testee()
        
        entry_id = cache.put_new_stream("search", "stream_url")
        self.assertEqual("stream_url", cache.retrieve(entry_id))

        second_entry = cache.put_new_stream("search 2", "stream_url 2")
        self.assertEqual("stream_url", cache.retrieve(entry_id))
        self.assertEqual("stream_url 2", cache.retrieve(second_entry))
        
    def test_add_retrieve(self):
        cache = self._testee()
        
        entry_id = cache.put_new_stream("search", "stream_url")
        
        self.assertTrue(cache.is_known(entry_id))
        self.assertTrue(cache.is_stream(entry_id))
        self.assertEqual("stream_url", cache.retrieve(entry_id))
        self.assertEqual(entry_id, cache.retrieve_id_by_search("search"))
        
        cache.add_filename(entry_id, "filename")
        self.assertTrue(cache.is_known(entry_id))
        self.assertFalse(cache.is_stream(entry_id))
        self.assertEqual("filename", cache.retrieve(entry_id))
        self.assertEqual(entry_id, cache.retrieve_id_by_search("search"))
        
    def test_errors(self):
        cache = self._testee()
        
        # error to insert same search again
        entry_id = cache.put_new_stream("search", "stream_url")
        try:
            cache.put_new_stream("search", "yet another url")
            self.fail("error")
        except ValueError:
            pass
            
        # it's an error to retrieve sth that is not there
        self.assertFalse(cache.retrieve("ausgedacht"))
        
        # it's an error to add a filename to sth that is not there
        try:
            cache.add_filename("ausgedacht", "bla")
            self.fail("error")
        except ValueError:
            pass
            