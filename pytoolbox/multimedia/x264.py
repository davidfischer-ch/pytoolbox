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

import datetime, re, shlex

from .ffmpeg import FFmpeg
from .. import module
from ..datetime import total_seconds
from ..encoding import string_types

_all = module.All(globals())

# [79.5%] 3276/4123 frames, 284.69 fps, 2111.44 kb/s, eta 0:00:02
ENCODING_REGEX = re.compile(
    r'\[(?P<percent>\d+\.\d*)%\]\s+(?P<frame>\d+)/(?P<frame_total>\d+)\s+frames,\s+'
    r'(?P<frame_rate>\d+\.\d*)\s+fps,\s+(?P<bit_rate>[^,]+),\s+eta\s+(?P<eta>[\d:]+)'
)


class X264(FFmpeg):

    encoding_regex = ENCODING_REGEX
    encoding_executable = 'x264'

    def _get_arguments(self, in_paths, out_path, options):
        in_paths = [f for f in ([in_paths] if isinstance(in_paths, string_types) else in_paths)]
        if len(in_paths) > 1:
            raise NotImplementedError('Unable to handle more than one input.')
        out_path = out_path or '/dev/null'
        options = (shlex.split(options) if isinstance(options, string_types) else options) or []
        args = [self.encoder_executable] + options + ['-o', out_path] + in_paths
        return args, in_paths, out_path, options

    def _get_progress(self, in_duration, stats):
        out_duration = in_duration * float(stats['percent'])
        ratio = float(stats['frame']) / float(stats['frame_total'])
        return out_duration, ratio

    def _clean_statistics(self, stats, **statistics):
        statistics.setdefault('eta_time', datetime.timedelta(seconds=total_seconds(stats['eta'])))
        return statistics

__all__ = _all.diff(globals())
