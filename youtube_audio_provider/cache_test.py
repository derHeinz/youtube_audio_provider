#!/usr/bin/python3
# -*- coding: utf

import unittest
from youtube_audio_provider.cache import Cache
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
