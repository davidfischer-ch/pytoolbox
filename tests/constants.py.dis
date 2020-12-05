import os, platform

__all__ = ['BITS', 'FFMPEG_ARCHIVE', 'FFMPEG_DIRECTORY', 'FFMPEG_URL', 'TESTS_DIRECTORY']

BITS = platform.architecture()[0]
TESTS_DIRECTORY = os.path.dirname(__file__)
FFMPEG_URL = f'http://johnvansickle.com/ffmpeg/releases/ffmpeg-2.5.4-{BITS}-static.tar.xz'
FFMPEG_ARCHIVE = os.path.join(TESTS_DIRECTORY, os.path.basename(FFMPEG_URL))
FFMPEG_DIRECTORY = FFMPEG_ARCHIVE.replace('.tar.xz', '')
