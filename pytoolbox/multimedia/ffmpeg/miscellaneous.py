from __future__ import annotations

from pathlib import Path
from typing import Any

from pytoolbox import comparison, filesystem, validation
from pytoolbox.subprocess import to_args_list, CallArgsType
from pytoolbox.types import get_slots

from . import utils

__all__ = [
    'BaseInfo',
    'Codec',
    'Format',
    'Stream',
    'AudioStream',
    'SubtitleStream',
    'VideoStream',
    'Media'
]


class BaseInfo(  # pylint:disable=too-few-public-methods
    validation.CleanAttributesMixin,
    comparison.SlotsEqualityMixin
):
    defaults: dict[str, Any] = {}
    attr_name_template: str = '{name}'

    def __init__(self, info: dict[str, Any]) -> None:
        for attr in get_slots(self):
            self._set_attribute(attr, info)

    def _set_attribute(self, name: str, info: dict) -> Any:
        """Set attribute `name` value from the `info` or ``self.defaults`` dictionary."""
        value = info.get(self.attr_name_template.format(name=name), self.defaults.get(name))
        setattr(self, name, value)
        return value


class Codec(BaseInfo):  # pylint:disable=too-few-public-methods
    long_name: str
    name: str
    tag: str
    tag_string: str
    time_base: float
    type: str

    __slots__ = ('long_name', 'name', 'tag', 'tag_string', 'time_base', 'type')

    attr_name_template: str = 'codec_{name}'

    def __init__(self, info: dict[str, Any]) -> None:
        # The codec_time_base is available (tested with ffprobe 4.3.1)
        if (attribute := self.attr_name_template.format(name='time_base')) in info:
            super().__init__(info)
        # Set codec_time_base to time_base (discovered with ffprobe 6.1)
        else:
            super().__init__({**info, attribute: info.get('time_base')})

    @staticmethod
    def clean_time_base(value: float | str | None) -> float | None:
        return None if value is None else utils.to_frame_rate(value)


class Format(BaseInfo):
    bit_rate: int | None
    duration: float | None
    filename: str
    format_name: str
    format_long_name: str
    nb_programs: int | None
    nb_streams: int | None
    probe_score: int | None
    size: int | None
    start_time: float | None
    tags: dict[str, str]

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
    avg_frame_rate: float | None
    bit_per_raw_sample: int | None
    bit_rate: int | None
    codec: Codec
    disposition: dict | None
    duration: float | None
    duration_ts: float | None
    index: int | None
    nb_frames: int | None
    profile: str | None
    r_frame_rate: float | None
    time_base: str | None
    tags: dict[str, str] | None

    __slots__ = (
        'avg_frame_rate',
        'bit_rate',
        'codec',
        'disposition',
        'duration',
        'duration_ts',
        'index',
        'nb_frames',
        'profile',
        'r_frame_rate',
        'time_base',
        'tags'
    )

    codec_class: type[Codec] = Codec

    def __init__(self, info: dict[str, Any]) -> None:  # pylint:disable=super-init-not-called
        for attr in get_slots(self):
            if attr == 'codec':
                self.codec = self.codec_class(info)
            else:
                self._set_attribute(attr, info)

    @staticmethod
    def clean_avg_frame_rate(value: float | str | None) -> float | None:
        return None if value is None else utils.to_frame_rate(value)

    @staticmethod
    def clean_bit_rate(value: int | str | None) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_duration(value: float | int | str | None) -> float | None:
        return None if value is None else float(value)

    @staticmethod
    def clean_duration_ts(value: int | str | None) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_index(value: int | str | None) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_nb_frames(value: int | str | None) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_r_frame_rate(value: float | str | None) -> float | None:
        return None if value is None else utils.to_frame_rate(value)


class AudioStream(Stream):
    bits_per_sample: int | None
    channel_layout: str | None
    channels: int | None
    sample_fmt: str | None
    sample_rate: int | None
    start_pts: int | None
    start_time: float | None

    __slots__ = (
        'bits_per_sample',
        'channel_layout',
        'channels',
        'sample_fmt',
        'sample_rate',
        'start_pts',
        'start_time'
    )

    @staticmethod
    def clean_bits_per_sample(value: int | str | None) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_channels(value: int | str | None) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_sample_rate(value: int | str | None) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_start_pts(value: int | str | None) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_start_time(value: float | int | str | None) -> float | None:
        return None if value is None else float(value)


class SubtitleStream(Stream):

    __slots__ = ('duration', 'duration_ts', 'start_pts', 'start_time', 'tags')

    @staticmethod
    def clean_duration(value: float | int | str | None) -> float | None:
        return None if value is None else float(value)

    @staticmethod
    def clean_duration_ts(value: int | str | None) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_start_pts(value: int | str | None) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_start_time(value: float | int | str | None) -> float | None:
        return None if value is None else float(value)


class VideoStream(Stream):

    __slots__ = (
        'bit_per_raw_sample',
        'display_aspect_ratio',
        'has_b_frames',
        'height',
        'level',
        'pix_fmt',
        'profile',
        'sample_aspect_ratio',
        'width'
    )

    @staticmethod
    def clean_bit_per_raw_sample(value: int | str | None) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_height(value: int | str | None) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_level(value: int | str | None) -> int | None:
        return None if value is None else int(value)

    @staticmethod
    def clean_width(value: int | str | None) -> int | None:
        return None if value is None else int(value)

    @property
    def rotation(self) -> int:
        tags = self.tags  # type: ignore[attr-defined]  # pylint:disable=no-member
        return int(0 if tags is None else tags.get('rotate', 0))


class Media(validation.CleanAttributesMixin, comparison.SlotsEqualityMixin):

    __slots__ = ('_path', 'options', '_is_pipe')

    def __init__(
        self,
        path: Path | str,
        options: CallArgsType | None = None
    ) -> None:
        self._is_pipe: bool = utils.is_pipe(path)
        self._path: Path | str = path if self._is_pipe else Path(path)
        self.options: list[str] = options or []  # type: ignore[assignment]
        self._size: int | None = None

    @property
    def directory(self) -> Path | None:
        if self.is_pipe:
            return None
        assert isinstance(self.path, Path)
        return self.path.resolve().parent

    @property
    def is_pipe(self) -> bool:
        return self._is_pipe

    @property
    def path(self) -> Path | str:
        return self._path

    @property
    def size(self) -> int:
        if self._size is not None:
            return self._size
        if self.is_pipe:
            return 0
        assert isinstance(self.path, Path)
        return filesystem.get_size(self.path)

    @size.setter
    def size(self, value: int | None) -> None:
        self._size = value

    @staticmethod
    def clean_options(value: CallArgsType) -> list[str]:
        return to_args_list(value)

    def create_directory(self) -> bool:
        if (directory := self.directory) is not None:
            return filesystem.makedirs(directory)
        return False

    def to_args(self, is_input: bool) -> list[str]:
        return self.options + (['-i', str(self.path)] if is_input else [str(self.path)])
