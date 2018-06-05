# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox.multimedia.x264 import ENCODING_REGEX

from . import base


class TestX264(base.TestCase):

    tags = ('multimedia', 'x264')

    def test_encoding_regex(self):
        match = ENCODING_REGEX.match('[79.5%] 3276/4123 frames, 284.69 fps, 2111.44 kb/s, eta 0:00:02')
        self.dict_equal(match.groupdict(), {
            'percent': '79.5', 'frame': '3276', 'frame_total': '4123', 'frame_rate': '284.69',
            'bit_rate': '2111.44 kb/s', 'eta': '0:00:02'
        })
