from __future__ import annotations

from pytoolbox.multimedia.x264 import ENCODING_REGEX


def test_encoding_regex() -> None:
    assert ENCODING_REGEX.match(
        '[79.5%] 3276/4123 frames, 284.69 fps, 2111.44 kb/s, eta 0:00:02').groupdict() == {
        'percent': '79.5',
        'frame': '3276',
        'frame_total': '4123',
        'frame_rate': '284.69',
        'bit_rate': '2111.44 kb/s',
        'eta': '0:00:02'
    }
