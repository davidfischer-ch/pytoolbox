from __future__ import annotations

from pathlib import Path

from pytoolbox import comparison, filesystem, module, validation
from pytoolbox.subprocess import to_args_list
from pytoolbox.types import get_slots
from . import utils

_all = module.All(globals())


class BaseInfo(  # pylint:disable=too-few-public-methods
    validation.CleanAttributesMixin,
    comparison.SlotsEqualityMixin
):

    defaults = {}
    attr_name_template = '{name}'

    def __init__(self, info: dict):
        for attr in get_slots(self):
            self._set_attribute(attr, info)

    def _set_attribute(self, name: str, info: dict) -> None:
        """Set attribute `name` value from the `info` or ``self.defaults`` dictionary."""
        value = info.get(self.attr_name_template.format(name=name), self.defaults.get(name))
        setattr(self, name, value)


class Codec(BaseInfo):  # pylint:disable=too-few-public-methods

    __slots__ = ('long_name', 'name', 'tag', 'tag_string', 'time_base', 'type')

    attr_name_template = 'codec_{name}'

    @staticmethod
    def clean_time_base(value) -> float | None:
        return None if value is None else utils.to_frame_rate(value)


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
    def clean_bit_rate(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_duration(value) -> float | None:
        return None if value is None else float(value)

    @staticmethod
    def clean_nb_programs(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_nb_streams(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_probe_score(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_size(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_start_time(value) -> float | None:
        return None if value is None else float(value)


class Stream(BaseInfo):

    __slots__ = ('avg_frame_rate', 'codec', 'disposition', 'index', 'r_frame_rate', 'time_base')

    codec_class = Codec

    def __init__(self, info: dict):  # pylint:disable=super-init-not-called
        for attr in get_slots(self):
            if attr == 'codec':
                self.codec = self.codec_class(info)
            else:
                self._set_attribute(attr, info)

    @staticmethod
    def clean_avg_frame_rate(value) -> float | None:
        return None if value is None else utils.to_frame_rate(value)

    @staticmethod
    def clean_index(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_r_frame_rate(value: str) -> float | None:
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
    def clean_bit_rate(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_bits_per_sample(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_channels(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_duration(value) -> float | None:
        return None if value is None else float(value)

    @staticmethod
    def clean_duration_ts(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_nb_frames(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_sample_rate(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_start_pts(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_start_time(value) -> float | None:
        return None if value is None else float(value)


class SubtitleStream(Stream):

    __slots__ = ('duration', 'duration_ts', 'start_pts', 'start_time', 'tags')

    @staticmethod
    def clean_duration(value) -> float | None:
        return None if value is None else float(value)

    @staticmethod
    def clean_duration_ts(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_start_pts(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_start_time(value) -> float | None:
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
    def clean_bit_rate(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_bit_per_raw_sample(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_duration(value) -> float | None:
        return None if value is None else float(value)

    @staticmethod
    def clean_duration_ts(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_height(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_level(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_nb_frames(value) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_width(value) -> int | None:
        return None if value is None else int(value)

    @property
    def rotation(self) -> int:
        tags = self.tags  # type: ignore[attr-defined]  # pylint:disable=no-member
        return int(0 if tags is None else tags.get('rotate', 0))


class Media(validation.CleanAttributesMixin, comparison.SlotsEqualityMixin):

    __slots__ = ('path', 'options')

    def __init__(self, path: Path | str, options=None):
        self.path: Path | str = path
        self.options: list[str] = options
        self._size: int | None = None

    @property
    def directory(self) -> Path | None:
        return None if self.is_pipe else Path(self.path).resolve().parent

    @property
    def is_pipe(self) -> bool:
        return utils.is_pipe(self.path)

    @property
    def size(self) -> int:
        if self._size is None:
            return 0 if self.is_pipe else filesystem.get_size(self.path)
        return self._size

    @size.setter
    def size(self, value: int | None):
        self._size = value

    @staticmethod
    def clean_options(value) -> list[str]:
        return to_args_list(value)

    def create_directory(self) -> None:
        if not self.is_pipe:
            filesystem.makedirs(self.directory)

    def to_args(self, is_input: bool) -> list[str]:
        return self.options + (['-i', str(self.path)] if is_input else [str(self.path)])


__all__ = _all.diff(globals())
