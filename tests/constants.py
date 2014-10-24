# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2014 David Fischer. All rights reserved.
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

import platform
from os.path import basename, dirname, join

__all__ = ('BITS', 'FFMPEG_ARCHIVE', 'FFMPEG_BINARY', 'FFMPEG_URL', 'TEST_ASSETS', 'TESTS_DIRECTORY')

BITS = platform.architecture()[0]
TESTS_DIRECTORY = dirname(__file__)
FFMPEG_URL = 'http://johnvansickle.com/ffmpeg/releases/ffmpeg-2.4.1-{0}-static.tar.xz'.format(BITS)
FFMPEG_ARCHIVE = join(TESTS_DIRECTORY, basename(FFMPEG_URL))
FFMPEG_BINARY = join(FFMPEG_ARCHIVE.replace('.tar.xz', ''), 'ffmpeg')

TEST_ASSETS = [
    ['http://techslides.com/demos/sample-videos/small.mp4', join(TESTS_DIRECTORY, 'small.mp4')]
]
