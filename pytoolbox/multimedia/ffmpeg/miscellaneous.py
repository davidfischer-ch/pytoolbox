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
        value = info.get(self.attr_name_template.format(name=name), self.defaults.get(name))
        setattr(self, name, value)


class Codec(BaseInfo):

    __slots__ = ('long_name', 'name', 'tag', 'tag_string', 'time_base', 'type')

    attr_name_template = 'codec_{name}'

    @staticmethod
    def clean_time_base(value):
        return utils.to_frame_rate(value)


class Format(BaseInfo):

    __slots__ = (
        'bit_rate',
        'duration',
        'filename',
        'format_name',
        'format_long_name',
        'nb_programs',
        'nb_streams',
        'probe_score',
        'size',
        'start_time',
        'tags'
    )

    @staticmethod
    def clean_bit_rate(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_duration(value):
        return None if value is None else float(value)

    @staticmethod
    def clean_nb_programs(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_nb_streams(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_probe_score(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_size(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_start_time(value):
        return None if value is None else float(value)


class Stream(BaseInfo):

    __slots__ = ('avg_frame_rate', 'codec', 'disposition', 'index', 'r_frame_rate', 'time_base')

    codec_class = Codec

    def __init__(self, info):  # pylint:disable=super-init-not-called
        for attr in get_slots(self):
            if attr == 'codec':
                self.codec = self.codec_class(info)
            else:
                self._set_attribute(attr, info)

    @staticmethod
    def clean_avg_frame_rate(value):
        return None if value is None else utils.to_frame_rate(value)

    @staticmethod
    def clean_index(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_r_frame_rate(value):
        return None if value is None else utils.to_frame_rate(value)


class AudioStream(Stream):

    __slots__ = (
        'bit_rate',
        'bits_per_sample',
        'channel_layout',
        'channels',
        'duration',
        'duration_ts',
        'nb_frames',
        'sample_fmt',
        'sample_rate',
        'start_pts',
        'start_time',
        'tags'
    )

    @staticmethod
    def clean_bit_rate(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_bits_per_sample(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_channels(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_duration(value):
        return None if value is None else float(value)

    @staticmethod
    def clean_duration_ts(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_nb_frames(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_sample_rate(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_start_pts(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_start_time(value):
        return None if value is None else float(value)


class SubtitleStream(Stream):

    __slots__ = ('duration', 'duration_ts', 'start_pts', 'start_time', 'tags')

    @staticmethod
    def clean_duration(value):
        return None if value is None else float(value)

    @staticmethod
    def clean_duration_ts(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_start_pts(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_start_time(value):
        return None if value is None else float(value)


class VideoStream(Stream):

    __slots__ = (
        'bit_rate',
        'bit_per_raw_sample',
        'display_aspect_ratio',
        'duration',
        'duration_ts',
        'has_b_frames',
        'height',
        'level',
        'nb_frames',
        'pix_fmt',
        'profile',
        'sample_aspect_ratio',
        'width',
        'tags'
    )

    @staticmethod
    def clean_bit_rate(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_bit_per_raw_sample(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_duration(value):
        return None if value is None else float(value)

    @staticmethod
    def clean_duration_ts(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_height(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_level(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_nb_frames(value):
        return None if value is None else int(value)

    @staticmethod
    def clean_width(value):
        return None if value is None else int(value)

    @property
    def rotation(self):
        tags = self.tags  # pylint:disable=no-member
        return int(0 if tags is None else tags.get('rotate', 0))


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

    @staticmethod
    def clean_options(value):
        return to_args_list(value)

    def create_directory(self):
        if not self.is_pipe:
            filesystem.makedirs(self.directory)

    def to_args(self, is_input):
        return self.options + (['-i', self.path] if is_input else [self.path])


__all__ = _all.diff(globals())
