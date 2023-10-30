#!/usr/bin/python3
# -*- coding: utf

import unittest
from youtube_audio_provider.appinfo import AppInfo


class TestAppInfo(unittest.TestCase):

    def _create_testee(self) -> AppInfo:
        return AppInfo()

    def test_get(self):
        default_result = self._create_testee().get()
        self.assertTrue(default_result.get('inittime'))
        self.assertEqual('foo'.upper(), 'FOO')
