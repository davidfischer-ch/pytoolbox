#!/usr/bin/env python
# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2015 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pytoolbox Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function, unicode_literals

import os, shutil, tarfile, tempfile

import six
from django.conf import settings

from pytoolbox.exceptions import BadHTTPResponseCodeError
from pytoolbox.network.http import download_ext
from pytoolbox.unittest import runtests

from . import constants


def main():
    print('Configure Django')
    settings.configure()

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
