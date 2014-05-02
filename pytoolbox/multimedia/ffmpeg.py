# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
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

import re, select, shlex, time
from subprocess import Popen, PIPE
from .ffprobe import get_media_duration
from ..datetime import datetime_now, str2time, time_ratio
from ..encoding import string_types
from ..filesystem import get_size
from ..subprocess import make_async

SIZE_REGEX = re.compile(ur'(?P<width>[0-9]+)x(?P<height>[0-9]+).*')
WIDTH, HEIGHT = range(2)  # The indexes of the width and the height in size [width, height]

# frame= 2071 fps=  0 q=-1.0 size=   34623kB time=00:01:25.89 bitrate=3302.3kbits/s
ENCODING_REGEX = re.compile(
    r'frame=\s*(?P<frame>\d+)\s+fps=\s*(?P<fps>\d+)\s+q=\s*(?P<q>\S+)\s+\S*size=\s*(?P<size>\S+)\s+'
    r'time=\s*(?P<time>\S+)\s+bitrate=\s*(?P<bitrate>\S+)')


def encode(in_filenames, out_filename, encoder_string, default_in_duration=u'00:00:00', time_format='%H:%M:%S',
           base_track=0, ratio_delta=0.01, time_delta=1, max_time_delta=5, sanity_min_ratio=0.95,
           sanity_max_ratio=1.05):

    if isinstance(in_filenames, string_types):
        in_filenames = [in_filenames]

    # Get input media duration and size to be able to estimate ETA
    in_duration = get_media_duration(in_filenames[base_track]) or str2time(default_in_duration)
    in_size = get_size(in_filenames[base_track])

    # Initialize metrics
    output = u''
    stats = {}
    start_date, start_time = datetime_now(), time.time()
    prev_ratio = prev_time = ratio = 0

    # Create FFmpeg subprocess
    in_filenames_string = u' '.join(u'-i "' + f + u'"' for f in in_filenames)
    cmd = u'ffmpeg -y {0} {1} "{2}"'.format(in_filenames_string, encoder_string, out_filename)
    ffmpeg = Popen(shlex.split(cmd), stderr=PIPE, close_fds=True)
    make_async(ffmpeg.stderr)

    while True:
        # Wait for data to become available
        select.select([ffmpeg.stderr], [], [])
        chunk = ffmpeg.stderr.read()
        output += chunk
        elapsed_time = time.time() - start_time
        match = ENCODING_REGEX.match(chunk)
        if match:
            stats = match.groupdict()
            out_duration = str2time(stats[u'time'])
            try:
                ratio = time_ratio(out_duration, in_duration)
            except ValueError:
                continue  # reported time is broken, skip the whole match
            delta_time = elapsed_time - prev_time
            if (ratio - prev_ratio > ratio_delta and delta_time > time_delta) or delta_time > max_time_delta:
                prev_ratio, prev_time = ratio, elapsed_time
                eta_time = int(elapsed_time * (1.0 - ratio) / ratio) if ratio > 0 else 0
                yield {
                    u'status': u'PROGRESS',
                    u'output': output,
                    u'returncode': None,
                    u'start_date': start_date,
                    u'elapsed_time': elapsed_time,
                    u'eta_time': eta_time,
                    u'in_size': in_size,
                    u'in_duration': in_duration.strftime(time_format),
                    u'out_size': get_size(out_filename),
                    u'out_duration': out_duration.strftime(time_format),
                    u'percent': int(100 * ratio),
                    u'frame': stats.get(u'frame'),
                    u'fps': stats.get(u'fps'),
                    u'bitrate': stats.get(u'bitrate'),
                    u'quality': stats.get(u'q'),
                    u'sanity': None
                }
        returncode = ffmpeg.poll()
        if returncode is not None:
            break

    # Output media file sanity check
    out_duration = get_media_duration(out_filename)
    ratio = time_ratio(out_duration, in_duration) if out_duration else 0.0
    yield {
        u'status': u'ERROR' if returncode else u'SUCCESS',
        u'output': output,
        u'returncode': returncode,
        u'start_date': start_date,
        u'elapsed_time': elapsed_time,
        u'eta_time': 0,
        u'in_size': in_size,
        u'in_duration': in_duration.strftime(time_format),
        u'out_size': get_size(out_filename),
        u'out_duration': out_duration.strftime(time_format) if out_duration else None,
        u'percent': int(100 * ratio) if returncode else 100,  # Assume that a successful encoding = 100%
        u'frame': stats.get(u'frame'),
        u'fps': stats.get(u'fps'),
        u'bitrate': stats.get(u'bitrate'),
        u'quality': stats.get(u'q'),
        u'sanity': sanity_min_ratio <= ratio <= sanity_max_ratio
    }
