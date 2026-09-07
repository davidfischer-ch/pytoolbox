"""
Encoding progress tracking and statistics for FFmpeg.
"""

from __future__ import annotations

import datetime
import re
import subprocess
import time
from typing import TYPE_CHECKING, Any, Final, TypedDict

from pytoolbox.compat import override
from pytoolbox.datetime import datetime_now, multiply_time, secs_to_time, str_to_time, time_ratio

from . import ffprobe, miscellaneous, utils

__all__ = [
    'ENCODING_REGEX',
    'EncodeState',
    'EncodeStatistics',
    'FFmpegStatistics',
    'FrameBasedRatioMixin',
]


class FFmpegStatistics(TypedDict):
    """One progress line of FFmpeg output, parsed into Python values."""

    time: datetime.timedelta | None
    frame: int
    frame_rate: float
    qscale: float | None
    size: int | None
    bit_rate: int | None


ENCODING_REGEX: Final[re.Pattern[str]] = re.compile(
    # frame= 2071 fps=  0 q=-1.0 size=   34623kB time=00:01:25.89 bitrate=3302.3kbits/s
    r'frame=\s*(?P<frame>\d+)\s+'
    r'fps=\s*(?P<frame_rate>\d+\.?\d*)\s+'
    r'q=\s*(?P<qscale>\S+)\s+\S*.*'
    r'size=\s*(?P<size>\S+)\s+'
    r'time=\s*(?P<time>\S+)\s+'
    r'bitrate=\s*(?P<bit_rate>\S+)',
)


class EncodeState:  # pylint:disable=too-few-public-methods
    """Enumeration of encoding process states."""

    NEW = 'NEW'
    STARTED = 'STARTED'
    PROCESSING = 'PROCESSING'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'

    ALL_STATES = frozenset([NEW, STARTED, PROCESSING, SUCCESS, FAILURE])
    FINAL_STATES = frozenset([SUCCESS, FAILURE])


class EncodeStatistics:  # pylint:disable=too-many-instance-attributes
    """Track and report FFmpeg encoding progress and statistics."""

    default_in_duration = datetime.timedelta(seconds=0)
    encoding_regex = ENCODING_REGEX
    ffprobe_class = ffprobe.FFprobe
    states = EncodeState

    def __init__(
        self,
        inputs: list[miscellaneous.Media],
        outputs: list[miscellaneous.Media],
        in_options: list[str],
        out_options: list[str],
        in_base_index: int = 0,
        out_base_index: int = 0,
    ) -> None:
        self.inputs = inputs
        self.outputs = outputs
        self.in_options = in_options
        self.out_options = out_options
        self.in_base_index = in_base_index
        self.out_base_index = out_base_index

        self.process: subprocess.Popen | None = None
        self.process_output: str = ''
        self.returncode: int | None = None

        self.state: str = self.states.NEW
        self.start_date: datetime.datetime | None = None
        self.start_time: float | None = None
        self.elapsed_time: datetime.timedelta | None = None
        self.ratio: float | None = None
        self.frame: int | None = None
        self.frame_rate: float | None = None
        self.qscale: float | None = None
        self.bit_rate: int | None = None

        # Retrieve input media duration and size, handle sub-clipping
        duration = self.ffprobe_class().get_media_duration(self.input, as_delta=True)
        duration = duration or self.default_in_duration
        self.input.duration, self.input.size = self._get_subclip_duration_and_size(
            duration,
            self.input.size,
            self.out_options,
        )
        self.output.duration = None

    @property
    def _started_at(self) -> float:
        """Return the monotonic start stamp, refusing to report on a run that never started."""
        if self.start_time is None:
            raise RuntimeError('The encoding was not started')
        return self.start_time

    @property
    def eta_time(self) -> datetime.timedelta | None:
        """Return the estimated time remaining or ``None`` if unknown."""
        if self.state in self.states.FINAL_STATES:
            return datetime.timedelta(0)
        if not self.ratio or self.elapsed_time is None:
            return None
        return multiply_time(self.elapsed_time, (1.0 - self.ratio) / self.ratio, as_delta=True)

    @property
    def input(self) -> miscellaneous.Media:
        """Return the primary input :class:`~.miscellaneous.Media`."""
        return self.inputs[self.in_base_index]

    @property
    def output(self) -> miscellaneous.Media:
        """Return the primary output :class:`~.miscellaneous.Media`."""
        return self.outputs[self.out_base_index]

    @staticmethod
    def get_now() -> datetime.datetime:
        """Return the current datetime."""
        return datetime_now(fmt=None)

    def start(self, process: subprocess.Popen) -> EncodeStatistics:
        """Record the start of encoding and initialize counters."""
        self.state = self.states.STARTED
        self.process = process
        self.start_date = self.get_now()
        self.start_time = time.time()
        self.elapsed_time = datetime.timedelta(0)
        self.output.duration = datetime.timedelta(0)
        self.frame = 0
        self._update_ratio()
        return self

    def progress(self, chunk: str) -> EncodeStatistics:
        """Update statistics from an FFmpeg output chunk."""
        self.state = self.states.PROCESSING
        self.elapsed_time = datetime.timedelta(seconds=time.time() - self._started_at)
        if ffmpeg_statistics := self._parse_chunk(chunk):
            self.output.duration = ffmpeg_statistics['time']
            self.frame = ffmpeg_statistics['frame']
            self.frame_rate = ffmpeg_statistics['frame_rate']
            self.qscale = ffmpeg_statistics['qscale']
            self.output.size = ffmpeg_statistics['size']
            self.bit_rate = ffmpeg_statistics['bit_rate']
        self._update_ratio()
        return self

    def end(self, returncode: int) -> EncodeStatistics:
        """Finalize statistics after encoding completes."""
        self.state = self.states.FAILURE if returncode else self.states.SUCCESS
        self.returncode = returncode
        self.elapsed_time = datetime.timedelta(seconds=time.time() - self._started_at)
        if self.frame is not None:
            self.frame_rate = self.frame / (self.elapsed_time.total_seconds() or 0.0001)
        self.output.duration = self.ffprobe_class().get_media_duration(
            self.output.path,
            as_delta=True,
        )
        self.output.size = None
        self._update_ratio()
        return self

    def _update_ratio(self) -> None:
        if self.state == self.states.SUCCESS:
            self.ratio = 1.0
        else:
            ratio = self._compute_ratio()
            self.ratio = None if ratio is None else min(1.0, max(0.0, ratio))

    def _compute_ratio(self) -> float | None:
        if self.input.duration and self.output.duration is not None:
            return time_ratio(self.output.duration, self.input.duration)
        return None

    @classmethod
    def _get_subclip_duration_and_size(
        cls,
        duration: datetime.timedelta,
        size: int,
        out_options: list[str],
    ) -> tuple[datetime.timedelta, int]:
        """Adjust duration and size if we only encode a sub-clip."""
        try:
            sub_duration = cls._to_time(out_options[out_options.index('-t') + 1])
        except (IndexError, ValueError):
            sub_duration = duration
        if sub_duration is None:
            return duration, size

        zero = datetime.timedelta(0)
        try:
            sub_position = cls._to_time(out_options[out_options.index('-ss') + 1]) or zero
        except (IndexError, ValueError):
            sub_position = zero

        sub_duration = max(zero, min(duration - sub_position, sub_duration))
        return sub_duration, int(size * time_ratio(sub_duration, duration))

    def _parse_chunk(self, chunk: str) -> FFmpegStatistics | None:
        self.process_output += chunk
        if not (match := self.encoding_regex.match(chunk.strip())):
            return None
        raw = match.groupdict()
        try:
            parsed_time = str_to_time(raw['time'], as_delta=True)
        except ValueError:
            return None  # Parsed statistics are broken, do not use them
        qscale = raw.get('qscale')
        return FFmpegStatistics(
            time=parsed_time,
            frame=int(raw['frame']),
            frame_rate=float(raw['frame_rate']),
            qscale=None if qscale is None else float(qscale),
            size=utils.to_size(raw['size']),
            bit_rate=utils.to_bit_rate(raw['bit_rate']),
        )

    @staticmethod
    def _to_time(value: str) -> datetime.timedelta | None:
        method = str_to_time if ':' in value else secs_to_time
        return method(value, as_delta=True)


# The mixin is designed to be combined with EncodeStatistics and reads its attributes. Naming
# that as the base under TYPE_CHECKING documents the requirement without making it one at
# runtime, where the mixin must stay to the left of the class it completes.
_FrameBasedRatioBase = EncodeStatistics if TYPE_CHECKING else object


class FrameBasedRatioMixin(_FrameBasedRatioBase):  # pylint:disable=too-few-public-methods
    """
    Compute ratio based on estimated input number of frames and current output number of frames.
    Fall-back to super's ratio computation method.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        fps = self.ffprobe_class().get_video_frame_rate(self.input)
        if fps and self.input.duration:
            self.input.frame = fps * self.input.duration.total_seconds()
        else:
            self.input.frame = None

    @override
    def _compute_ratio(self) -> float | None:
        if self.input.frame and self.frame is not None:
            return self.frame / self.input.frame
        return super()._compute_ratio()
