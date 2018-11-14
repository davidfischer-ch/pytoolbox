# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import os

from pytoolbox import comparison, filesystem, module, validation
from pytoolbox.subprocess import to_args_list
from pytoolbox.types import get_slots

from . import utils

_all = module.All(globals())


class BaseInfo(validation.CleanAttributesMixin, comparison.SlotsEqualityMixin):

    defaults = {}
    attr_name_template = '{name}'

    def __init__(self, info):
        for attr in get_slots(self):
            self._set_attribute(attr, info)

    def _set_attribute(self, name, info):
        """Set attribute `name` value from the `info` or ``self.defaults`` dictionary."""
        setattr(self, name, info.get(
            self.attr_name_template.format(name=name), self.defaults.get(name)))


class Codec(BaseInfo):

    __slots__ = ('long_name', 'name', 'tag', 'tag_string', 'time_base', 'type')

    attr_name_template = 'codec_{name}'
    clean_time_base = lambda s, v: utils.to_frame_rate(v)


class Format(BaseInfo):

    __slots__ = (
        'bit_rate', 'duration', 'filename', 'format_name', 'format_long_name', 'nb_programs',
        'nb_streams', 'probe_score', 'size', 'start_time'
    )

    clean_bit_rate = clean_nb_programs = clean_nb_streams = clean_probe_score = clean_size = \
        lambda s, v: None if v is None else int(v)
    clean_duration = clean_start_time = lambda s, v: None if v is None else float(v)


class Stream(BaseInfo):

    __slots__ = ('avg_frame_rate', 'codec', 'disposition', 'index', 'r_frame_rate', 'time_base')

    codec_class = Codec

    def __init__(self, info):
        for attr in get_slots(self):
            if attr == 'codec':
                self.codec = self.codec_class(info)
            else:
                self._set_attribute(attr, info)

    clean_avg_frame_rate = clean_r_frame_rate = clean_time_base = (
        lambda s, v: None if v is None else utils.to_frame_rate(v)
    )
    clean_index = lambda s, v: None if v is None else int(v)


class AudioStream(Stream):

    __slots__ = (
        'bit_rate', 'bits_per_sample', 'channel_layout', 'channels', 'duration', 'duration_ts',
        'nb_frames', 'sample_fmt', 'sample_rate', 'start_pts', 'start_time', 'tags'
    )

    clean_bit_rate = clean_bits_per_sample = clean_channels = clean_duration_ts = \
        clean_nb_frames = clean_sample_rate = clean_start_pts = \
        lambda s, v: None if v is None else int(v)
    clean_duration = clean_start_time = lambda s, v: None if v is None else float(v)


class SubtitleStream(Stream):

    __slots__ = ('duration', 'duration_ts', 'start_pts', 'start_time', 'tags')

    clean_duration_ts = clean_start_pts = lambda s, v: None if v is None else int(v)
    clean_duration = clean_start_time = lambda s, v: None if v is None else float(v)


class VideoStream(Stream):

    __slots__ = (
        'display_aspect_ratio', 'has_b_frames', 'height', 'level', 'nb_frames', 'pix_fmt',
        'sample_aspect_ratio', 'width'
    )

    clean_height = clean_level = clean_nb_frames = clean_width = \
        lambda s, v: None if v is None else int(v)


class Media(validation.CleanAttributesMixin, comparison.SlotsEqualityMixin):

    __slots__ = ('path', 'options')

    def __init__(self, path, options=None):
        self.path = path
        self.options = options
        self._size = None

    @property
    def directory(self):
        return None if self.is_pipe else os.path.abspath(os.path.dirname(self.path))

    @property
    def is_pipe(self):
        return utils.is_pipe(self.path)

    @property
    def size(self):
        if self._size is None:
            return 0 if self.is_pipe else filesystem.get_size(self.path)
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    def clean_options(self, value):
        return to_args_list(value)

    def create_directory(self):
        if not self.is_pipe:
            filesystem.makedirs(self.directory)

    def to_args(self, is_input):
        return self.options + (['-i', self.path] if is_input else [self.path])


__all__ = _all.diff(globals())
