#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import json
import datetime

import unittest

from youtube_audio_provider.appinfo import AppInfo

class TestAppInfo(unittest.TestCase):

    def _createTestee(self) -> AppInfo:
        return AppInfo()

    def test_get(self):
        default_result = self._createTestee().get()
        self.assertTrue(default_result.get('inittime'))
        self.assertEqual('foo'.upper(), 'FOO')
