# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import os, platform

__all__ = ('BITS', 'FFMPEG_ARCHIVE', 'FFMPEG_DIRECTORY', 'FFMPEG_URL', 'TEST_ASSETS', 'TESTS_DIRECTORY')

BITS = platform.architecture()[0]
TESTS_DIRECTORY = os.path.dirname(__file__)
FFMPEG_URL = 'http://johnvansickle.com/ffmpeg/releases/ffmpeg-2.5.4-{0}-static.tar.xz'.format(BITS)
FFMPEG_ARCHIVE = os.path.join(TESTS_DIRECTORY, os.path.basename(FFMPEG_URL))
FFMPEG_DIRECTORY = FFMPEG_ARCHIVE.replace('.tar.xz', '')

TEST_ASSETS = [
    ['http://techslides.com/demos/sample-videos/small.mp4', os.path.join(TESTS_DIRECTORY, 'small.mp4')]
]
