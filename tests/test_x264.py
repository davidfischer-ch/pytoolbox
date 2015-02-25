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

import unittest
from pytoolbox.multimedia.x264 import ENCODING_REGEX


class TestX264(unittest.TestCase):

    def test_encoding_regex(self):
        match = ENCODING_REGEX.match('[79.5%] 3276/4123 frames, 284.69 fps, 2111.44 kb/s, eta 0:00:02')
        self.assertDictEqual(match.groupdict(), {
            'percent': '79.5', 'frame': '3276', 'frame_total': '4123', 'fps': '284.69', 'bitrate': '2111.44 kb/s',
            'eta': '0:00:02'
        })
