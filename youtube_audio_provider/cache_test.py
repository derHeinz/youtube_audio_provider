#!/usr/bin/python3
# -*- coding: utf

import unittest
from youtube_audio_provider.cache import Cache, Item
from youtube_audio_provider.appinfo import AppInfo


class TestCache(unittest.TestCase):

    class NoopExporter:

        def export(self, data):
            pass

    class NonPersistentCache(Cache):
        ''' creates a cache that does not persist'''

        def __init__(self, *args, **kwargs):
            super(TestCache.NonPersistentCache, self).__init__(*args, **kwargs)

        def _load_cache_from_disk(self):
            pass

        def _store_cache_to_disk(self):
            pass

        def _check_file_exists(self, filename):
            return True

    def _create_testee(self) -> NonPersistentCache:
        return TestCache.NonPersistentCache(TestCache.NoopExporter(), AppInfo(), '')

    def test_put_retrieve_remove(self):
        testee = self._create_testee()
        testee.put_to_cache('qqq', 'my-file')

        filename = testee.retrieve_from_cache('qqq')
        self.assertEqual('my-file', filename)

        testee.remove_from_cache_by_search('qqq')
        filename = testee.retrieve_from_cache('qqq')
        self.assertIsNone(filename)

    def test_case_insensitiv(self):
        testee = self._create_testee()
        testee.put_to_cache('QQQ', 'my-file')

        filename = testee.retrieve_from_cache('qqq')
        self.assertEqual('my-file', filename)

        filename = testee.retrieve_from_cache('QqQ')
        self.assertEqual('my-file', filename)

    def test_appinfo_contains_size(self):
        testee = self._create_testee()

        self.assertEqual(0, testee.appinfo.get()['cache_size'])
        testee.put_to_cache('qqq', 'my-file')
        self.assertEqual(1, testee.appinfo.get()['cache_size'])
        testee.remove_from_cache_by_search('qqq')
        self.assertEqual(0, testee.appinfo.get()['cache_size'])

    def test_fulltext_search(self):
        testee = self._create_testee()

        self.assertEqual(0, testee.appinfo.get()['cache_size'])
        song_1 = 'The Electric Dreamers - Stardust Serenade.mp3'
        phrase_1 = 'asdf'
        testee.put_to_cache(phrase_1, song_1)
        song_2 = 'Luna Shadows - Nebula Whispers.mp3'
        phrase_2 = 'Lovin%20Luna'
        testee.put_to_cache(phrase_2, song_2)
        song_3 = 'Echo Synthesis - Binary Love.mp3'
        phrase_3 = 'binary%20love'
        testee.put_to_cache(phrase_3, song_3)
        song_4 = song_3
        phrase_4 = 'echo%20love'
        testee.put_to_cache(phrase_4, song_4)
        song_5 = 'Midnight Voyager - Celestial Echoes.mp3'
        phrase_5 = 'mid%20night%20echo'
        testee.put_to_cache(phrase_5, song_5)
        song_6 = 'Quantum Beats Collective - Hyperspace Groove.mp3'
        phrase_6 = 'quantum-beats'
        testee.put_to_cache(phrase_6, song_6)
        self.assertEqual(6, testee.appinfo.get()['cache_size'])

        # 1 result exact match
        res = testee.fulltext_search(song_6)
        self.assertEqual(1, len(res))
        self.assertTrue(Item(phrase_6, song_6) in res)

        # artist only, 2 results becaues of exact=False?
        res = testee.fulltext_search('Echo Synthesis')
        self.assertEqual(2, len(res))
        self.assertTrue(Item(phrase_3, song_3) in res)
        self.assertTrue(Item(phrase_5, song_5) in res)

        # duplicates, word-parts, 2 results
        res = testee.fulltext_search('Echo')
        self.assertEqual(2, len(res))
        self.assertTrue(Item(phrase_3, song_3) in res)
        self.assertTrue(Item(phrase_5, song_5) in res)

    def test_put_remove_fulltext_search(self):
        testee = self._create_testee()

        # simple put/remove
        testee.put_to_cache('qqq', 'my file')
        res = testee.fulltext_search('file')
        self.assertEqual(1, len(res))
        self.assertTrue(Item('qqq', 'my file') in res)
        testee.remove_from_cache_by_search('qqq')
        res = testee.fulltext_search('file')
        self.assertEqual(0, len(res))

        # put several
        testee.put_to_cache('qqq', 'my file')
        testee.put_to_cache('rrr', 'my file')
        res = testee.fulltext_search('file')
        self.assertEqual(1, len(res))
        testee.remove_from_cache_by_search('qqq')
        res = testee.fulltext_search('file')
        self.assertEqual(0, len(res))
