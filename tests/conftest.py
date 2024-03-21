from __future__ import annotations

from pathlib import Path
from typing import Final
import platform
import tarfile

import pytest
from pytoolbox import filesystem
from pytoolbox.multimedia import ffmpeg
from pytoolbox.network import http

BITS: Final[str] = {'x86_64': 'amd64'}[platform.processor()]
TEST_S3_URL: Final[str] = 'https://pytoolbox.s3-eu-west-1.amazonaws.com/tests'
TMP_DIRECTORY: Final[Path] = Path(__file__).resolve().parent / '.tmp'

# Credits: https://johnvansickle.com/ffmpeg/
FFMPEG_VERSION: Final[str] = '4.3.1'
FFMPEG_ARCHIVE_NAME: Final[str] = f'ffmpeg-{FFMPEG_VERSION}-{BITS}-static'
FFMPEG_RELEASE_URL: Final[str] = f'{TEST_S3_URL}/{FFMPEG_ARCHIVE_NAME}.tar.xz'
FFMPEG_RELEASE_ARCHIVE: Final[Path] = TMP_DIRECTORY / f'{FFMPEG_ARCHIVE_NAME}.tar.xz'
FFMPEG_RELEASE_CHECKSUM: Final[str] = {'amd64': 'ee235393ec7778279144ee6cbdd9eb64'}[BITS]
FFMPEG_RELEASE_DIRECTORY: Final[Path] = TMP_DIRECTORY / f'ffmpeg-{FFMPEG_VERSION}-{BITS}-static'

# Credits: http://techslides.com/demos/sample-videos/small.mp4
SMALL_MP4_URL: Final[str] = f'{TEST_S3_URL}/small.mp4'
SMALL_MP4_CHECKSUM: Final[str] = 'a3ac7ddabb263c2d00b73e8177d15c8d'
SMALL_MP4_FILENAME: Final[Path] = TMP_DIRECTORY / 'small.mp4'


def download_static_ffmpeg():
    print('Download ffmpeg static binary')
    filesystem.makedirs(TMP_DIRECTORY)
    http.download_ext(
        FFMPEG_RELEASE_URL,
        FFMPEG_RELEASE_ARCHIVE,
        expected_hash=FFMPEG_RELEASE_CHECKSUM,
        hash_algorithm='md5',
        force=False)
    with tarfile.open(FFMPEG_RELEASE_ARCHIVE) as f:
        f.extractall(TMP_DIRECTORY)


# TODO Promote it to the library (merge)
class StaticFFprobe(ffmpeg.FFprobe):
    executable = FFMPEG_RELEASE_DIRECTORY / 'ffprobe'


# TODO Promote it to the library (merge)
class StaticEncodeStatistics(ffmpeg.EncodeStatistics):
    ffprobe_class = StaticFFprobe


# TODO Promote it to the library (merge)
class StaticEncodeStatisticsWithFrameBaseRatio(
    ffmpeg.FrameBasedRatioMixin,
    StaticEncodeStatistics
):
    pass


# TODO Promote it to the library (merge)
class StaticFFmpeg(ffmpeg.FFmpeg):
    executable = FFMPEG_RELEASE_DIRECTORY / 'ffmpeg'
    ffprobe_class = StaticFFprobe
    statistics_class = StaticEncodeStatistics


@pytest.fixture(scope='session')
def static_ffmpeg(request) -> type[StaticFFmpeg]:  # pylint:disable=unused-argument
    download_static_ffmpeg()
    return StaticFFmpeg


@pytest.fixture(scope='function')
def statistics(  # pylint:disable=redefined-outer-name
    small_mp4: Path,
    tmp_path: Path
) -> StaticEncodeStatistics:
    return StaticEncodeStatistics(
        [ffmpeg.Media(small_mp4)],
        [ffmpeg.Media(tmp_path / 'output.mp4')],
        [],
        ['-acodec', 'copy', '-vcodec', 'copy'])


@pytest.fixture(scope='function')
def frame_based_statistics(  # pylint:disable=redefined-outer-name,too-few-public-methods
    small_mp4: Path,
    tmp_path: Path
) -> StaticEncodeStatisticsWithFrameBaseRatio:
    return StaticEncodeStatisticsWithFrameBaseRatio(
        [ffmpeg.Media(small_mp4)],
        [ffmpeg.Media(tmp_path / 'output.mp4')],
        [],
        ['-acodec', 'copy', '-vcodec', 'copy'])


@pytest.fixture(scope='session')
def small_mp4(request) -> Path:  # pylint:disable=unused-argument
    print('Download small.mp4')
    filesystem.makedirs(TMP_DIRECTORY)
    http.download_ext(
        SMALL_MP4_URL,
        SMALL_MP4_FILENAME,
        expected_hash=SMALL_MP4_CHECKSUM,
        hash_algorithm='md5',
        force=False)
    return SMALL_MP4_FILENAME
