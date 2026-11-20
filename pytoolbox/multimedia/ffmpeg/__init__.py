"""
FFmpeg and FFprobe wrappers for media encoding and inspection.
"""

from __future__ import annotations

from .encode import (  # noqa: F401
    ENCODING_PATTERN,
    EncodeState,
    EncodeStatistics,
    FrameBasedRatioMixin,
)
from .ffmpeg import FRAME_MD5_PATTERN, FFmpeg  # noqa: F401
from .ffprobe import DURATION_PATTERN, FFprobe  # noqa: F401
from .miscellaneous import (  # noqa: F401
    AudioStream,
    BaseInfo,
    Codec,
    Format,
    Media,
    Stream,
    SubtitleStream,
    VideoStream,
)
from .utils import (  # noqa: F401
    BIT_RATE_COEFFICIENT_FOR_UNIT,
    BIT_RATE_PATTERN,
    HEIGHT,
    PIPE_PATTERN,
    SIZE_COEFFICIENT_FOR_UNIT,
    SIZE_PATTERN,
    WIDTH,
    is_pipe,
    to_bit_rate,
    to_frame_rate,
    to_size,
)
