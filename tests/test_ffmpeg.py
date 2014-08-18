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

from nose.tools import eq_, assert_raises as ar_
from pytoolbox.filesystem import try_remove
from pytoolbox.multimedia.ffmpeg import FFmpeg


class RaiseFFmpeg(FFmpeg):

    def _clean_statistics(self, **statistics):
        raise ValueError('This is the exception.')


class TestFFmpeg(object):

    def test_kill_process_handle_missing(self):
        encoder = RaiseFFmpeg()
        with ar_(ValueError):
            list(encoder.encode('small.mp4', 'ff_output.mp4', '-c:a copy -c:v copy'))
        eq_(try_remove('ff_output.mp4'), True)
