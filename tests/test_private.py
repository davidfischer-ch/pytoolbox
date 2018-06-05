# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox.private import _parse_kwargs_string

from . import base


class TestPrivate(base.TestCase):

    tags = ('private', )

    def test_parse_kwargs_string(self):
        self.dict_equal(_parse_kwargs_string('year=1950 ;  style=jazz', year=int, style=str), {
            'year': 1950, 'style': 'jazz'
        })
        self.dict_equal(_parse_kwargs_string(' like_it=True ', like_it=lambda x: x == 'True'), {'like_it': True})

    def test_parse_kwargs_string_key_error(self):
        with self.raises(KeyError):
            _parse_kwargs_string(' pi=3.1416; ru=2', pi=float)

    def test_parse_kwargs_string_value_error(self):
        with self.raises(ValueError):
            _parse_kwargs_string(' a_number=yeah', a_number=int)
