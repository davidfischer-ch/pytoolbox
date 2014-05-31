# -*- coding: utf-8 -*-

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

import re, select, shlex, time
from subprocess import Popen, PIPE
from .ffprobe import get_media_duration
from ..datetime import datetime_now, str2time, time_ratio
from ..encoding import string_types
from ..filesystem import get_size
from ..subprocess import make_async

SIZE_REGEX = re.compile(r'(?P<width>[0-9]+)x(?P<height>[0-9]+).*')
WIDTH, HEIGHT = range(2)  # The indexes of the width and the height in size [width, height]

# frame= 2071 fps=  0 q=-1.0 size=   34623kB time=00:01:25.89 bitrate=3302.3kbits/s
ENCODING_REGEX = re.compile(
    r'frame=\s*(?P<frame>\d+)\s+fps=\s*(?P<fps>\d+)\s+q=\s*(?P<q>\S+)\s+\S*size=\s*(?P<size>\S+)\s+'
    r'time=\s*(?P<time>\S+)\s+bitrate=\s*(?P<bitrate>\S+)')


def encode(in_filenames, out_filename, encoder_string, default_in_duration='00:00:00', time_format='%H:%M:%S',
           base_track=0, ratio_delta=0.01, time_delta=1, max_time_delta=5, sanity_min_ratio=0.95,
           sanity_max_ratio=1.05):

    if isinstance(in_filenames, string_types):
        in_filenames = [in_filenames]

    # Get input media duration and size to be able to estimate ETA
    in_duration = get_media_duration(in_filenames[base_track]) or str2time(default_in_duration)
    in_size = get_size(in_filenames[base_track])

    # Initialize metrics
    output = ''
    stats = {}
    start_date, start_time = datetime_now(), time.time()
    prev_ratio = prev_time = ratio = 0

    # Create FFmpeg subprocess
    in_filenames_string = ' '.join('-i "' + f + '"' for f in in_filenames)
    cmd = 'ffmpeg -y {0} {1} "{2}"'.format(in_filenames_string, encoder_string, out_filename)
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
            try:
                out_duration = str2time(stats['time'])
                ratio = time_ratio(out_duration, in_duration)
            except ValueError:
                continue  # reported time is broken, skip the whole match
            delta_time = elapsed_time - prev_time
            if (ratio - prev_ratio > ratio_delta and delta_time > time_delta) or delta_time > max_time_delta:
                prev_ratio, prev_time = ratio, elapsed_time
                eta_time = int(elapsed_time * (1.0 - ratio) / ratio) if ratio > 0 else 0
                yield {
                    'status': 'PROGRESS',
                    'output': output,
                    'returncode': None,
                    'start_date': start_date,
                    'elapsed_time': elapsed_time,
                    'eta_time': eta_time,
                    'in_size': in_size,
                    'in_duration': in_duration.strftime(time_format),
                    'out_size': get_size(out_filename),
                    'out_duration': out_duration.strftime(time_format),
                    'percent': int(100 * ratio),
                    'frame': stats.get('frame'),
                    'fps': stats.get('fps'),
                    'bitrate': stats.get('bitrate'),
                    'quality': stats.get('q'),
                    'sanity': None
                }
        returncode = ffmpeg.poll()
        if returncode is not None:
            break

    # Output media file sanity check
    out_duration = get_media_duration(out_filename)
    ratio = time_ratio(out_duration, in_duration) if out_duration else 0.0
    yield {
        'status': 'ERROR' if returncode else 'SUCCESS',
        'output': output,
        'returncode': returncode,
        'start_date': start_date,
        'elapsed_time': elapsed_time,
        'eta_time': 0,
        'in_size': in_size,
        'in_duration': in_duration.strftime(time_format),
        'out_size': get_size(out_filename),
        'out_duration': out_duration.strftime(time_format) if out_duration else None,
        'percent': int(100 * ratio) if returncode else 100,  # Assume that a successful encoding = 100%
        'frame': stats.get('frame'),
        'fps': stats.get('fps'),
        'bitrate': stats.get('bitrate'),
        'quality': stats.get('q'),
        'sanity': sanity_min_ratio <= ratio <= sanity_max_ratio
    }
