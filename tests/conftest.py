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
FFMPEG_VERSION: Final[str] = '6.1'
FFMPEG_RELEASE_URL: Final[str] = f'{TEST_S3_URL}/ffmpeg-{FFMPEG_VERSION}-{BITS}-static.tar.xz'
FFMPEG_RELEASE_EXTENSION: Final[str] = '.tar.xz'
FFMPEG_RELEASE_CHECKSUM: Final[tuple[str, str]] = {
    'amd64': ('md5', '8a34e2ab52b72777a8dcd3ff5defbcd8')
}[BITS]

# Credits: http://techslides.com/demos/sample-videos/small.mp4
SMALL_MP4_URL: Final[str] = f'{TEST_S3_URL}/small.mp4'
SMALL_MP4_CHECKSUM: Final[tuple[str, str]] = ('md5', 'a3ac7ddabb263c2d00b73e8177d15c8d')
SMALL_MP4_FILENAME: Final[Path] = TMP_DIRECTORY / 'small.mp4'


# TODO Promote it to the library (merge)
class DownloadStaticFFmpegMixin(object):  # pylint:disable=too-few-public-methods
    executable: Path

    def __init__(self, *args, **kwargs) -> None:
        executable = self.download_static_ffmpeg()
        super().__init__(executable=executable, *args, **kwargs)  # type: ignore[call-arg]

    @classmethod
    def download_static_ffmpeg(
        cls,
        archive_url: str = FFMPEG_RELEASE_URL,
        archive_extension: str = FFMPEG_RELEASE_EXTENSION,
        directory: Path = TMP_DIRECTORY,
        expected_hash: str = FFMPEG_RELEASE_CHECKSUM[1],
        hash_algorithm: str = FFMPEG_RELEASE_CHECKSUM[0]
    ) -> Path:
        filesystem.makedirs(directory)
        archive = directory / archive_url.split('/')[-1]  # Get archive filename from URL
        archive_name = archive.name.removesuffix(archive_extension)
        executable = archive.parent / archive_name / cls.executable.name
        _, downloaded, _ = http.download_ext(
            url=archive_url,
            path=archive,
            expected_hash=expected_hash,
            hash_algorithm=hash_algorithm,
            force=False)
        if downloaded:
            print('Downloaded ffmpeg static binary')
        if downloaded or not executable.exists():
            with tarfile.open(archive) as f:
                f.extractall(directory)
            print('Extracted ffmpeg static binary')
        if not executable.exists():
            raise RuntimeError(f"Executable {executable} not found.")
        return executable


# TODO Promote it to the library (merge)
class StaticFFprobe(DownloadStaticFFmpegMixin, ffmpeg.FFprobe):
    pass


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
class StaticFFmpeg(DownloadStaticFFmpegMixin, ffmpeg.FFmpeg):
    ffprobe_class = StaticFFprobe
    statistics_class = StaticEncodeStatistics


@pytest.fixture(scope='session')
def static_ffmpeg(request) -> type[StaticFFmpeg]:  # pylint:disable=unused-argument
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
        expected_hash=SMALL_MP4_CHECKSUM[1],
        hash_algorithm=SMALL_MP4_CHECKSUM[0],
        force=False)
    return SMALL_MP4_FILENAME
