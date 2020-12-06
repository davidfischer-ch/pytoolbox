import platform, tarfile
from pathlib import Path

import pytest
from pytoolbox import filesystem
from pytoolbox.multimedia import ffmpeg
from pytoolbox.network import http

BITS = {'x86_64': 'amd64'}[platform.processor()]
TMP_DIRECTORY = Path(__file__).resolve().parent / '.tmp'

# Credits: https://johnvansickle.com/ffmpeg/
FFMPEG_URL = f'https://pytoolbox.s3-eu-west-1.amazonaws.com/tests/ffmpeg-4.3.1-{BITS}-static.tar.xz'
FFMPEG_HASH = {'amd64': 'ee235393ec7778279144ee6cbdd9eb64'}[BITS]
FFMPEG_ARCHIVE = TMP_DIRECTORY / f'ffmpeg-4.3.1-{BITS}-static.tar.xz'
FFMPEG_DIRECTORY = TMP_DIRECTORY / f'ffmpeg-4.3.1-{BITS}-static'

# Credits: http://techslides.com/demos/sample-videos/small.mp4
SMALL_URL = 'https://pytoolbox.s3-eu-west-1.amazonaws.com/tests/small.mp4'
SMALL_HASH = 'a3ac7ddabb263c2d00b73e8177d15c8d'
SMALL_FILENAME = TMP_DIRECTORY / 'small.mp4'


@pytest.fixture(scope='session')
def ffmpeg_release(request):  # pylint:disable=unused-argument
    print('Download ffmpeg static binary')
    filesystem.makedirs(TMP_DIRECTORY)
    http.download_ext(
        FFMPEG_URL,
        FFMPEG_ARCHIVE,
        expected_hash=FFMPEG_HASH,
        hash_algorithm='md5',
        force=False)
    with tarfile.open(FFMPEG_ARCHIVE) as f:
        f.extractall(TMP_DIRECTORY)

    class StaticFFmpeg(ffmpeg.FFmpeg):
        executable = FFMPEG_DIRECTORY / 'ffmpeg'

    class StaticFFprobe(ffmpeg.FFprobe):
        executable = FFMPEG_DIRECTORY / 'ffprobe'

    return StaticFFmpeg, StaticFFprobe


@pytest.fixture(scope='session')
def small_mp4(request):  # pylint:disable=unused-argument
    print('Download small.mp4')
    filesystem.makedirs(TMP_DIRECTORY)
    http.download_ext(
        SMALL_URL,
        SMALL_FILENAME,
        expected_hash=SMALL_HASH,
        hash_algorithm='md5',
        force=False)
    return SMALL_FILENAME
