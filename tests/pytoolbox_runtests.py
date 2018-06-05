#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import os, shutil, tarfile, tempfile

import six

from pytoolbox.exceptions import BadHTTPResponseCodeError
from pytoolbox.network.http import download_ext
from pytoolbox.unittest import runtests

from . import constants


def main():
    print('Configure Django')
    try:
        from django.conf import settings
        settings.configure()
    except ImportError:
        print('WARNING: Django not available for testing purposes')

    print('Download the test assets')
    for url, path in constants.TEST_ASSETS:
        download_ext(url, path, force=False)

    print('Download ffmpeg static binary')
    try:
        download_ext(constants.FFMPEG_URL, constants.FFMPEG_ARCHIVE, force=False)
        if six.PY2:
            import contextlib
            try:
                import lzma
            except ImportError:
                from backports import lzma
            with contextlib.closing(lzma.LZMAFile(constants.FFMPEG_ARCHIVE)) as xz:
                with tarfile.open(fileobj=xz) as f:
                    f.extractall(constants.TESTS_DIRECTORY)
        else:
            with tarfile.open(constants.FFMPEG_ARCHIVE) as f:
                f.extractall(constants.TESTS_DIRECTORY)
        for path in 'ffmpeg', 'ffprobe':
            shutil.copy(os.path.join(constants.FFMPEG_DIRECTORY, path), tempfile.gettempdir())
    except BadHTTPResponseCodeError:
        print('Unable to download ffmpeg: Will mock ffmpeg if missing')

    print('Run the tests with nose')
    return runtests(__file__, cover_packages=['pytoolbox'], packages=['pytoolbox', 'tests'])

if __name__ == '__main__':
    main()
