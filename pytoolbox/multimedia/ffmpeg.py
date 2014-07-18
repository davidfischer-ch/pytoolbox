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


def get_subprocess(in_filenames, out_filename, options, executable='ffmpeg'):
    """
    Return a ffmpeg subprocess with stderr made asynchronous.

    * Set in_filenames to a string or a "list" with the input filenames.
    * Set out_filename to a string.
    * Set argument to a string or a list with the options for ffmpeg (except ones related to input(s) / output).

    In return you will get a tuple with (subprocess, in_filenames -> list, options -> list).
    This function ensure subprocess.args is set to the arguments of the ffmpeg subprocess.

    **Example usage**

    >>> from nose.tools import assert_list_equal as leq_
    >>> options_string = '-strict experimental -vf "yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2"'

    >>> ffmpeg, in_filenames, options = get_subprocess('input.mp4', 'output.mkv', options_string)
    >>> leq_(in_filenames, ['input.mp4'])
    >>> leq_(options, ['-strict', 'experimental', '-vf', 'yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2'])
    >>> leq_(ffmpeg.args, ['ffmpeg', '-y', '-i', 'input.mp4'] + options + ['output.mkv'])
    >>> ffmpeg.kill()

    >>> ffmpeg, in_filenames, options = get_subprocess({'input.avi'}, 'output.mp4', options_string)
    >>> leq_(in_filenames, ['input.avi'])
    >>> leq_(options, ['-strict', 'experimental', '-vf', 'yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2'])
    >>> leq_(ffmpeg.args, ['ffmpeg', '-y', '-i', 'input.avi'] + options + ['output.mp4'])
    >>> ffmpeg.kill()

    >>> ffmpeg, in_filenames, options = get_subprocess(('video.h264', 'audio.mp3'), 'output.mp4', options)
    >>> leq_(sorted(in_filenames), ['audio.mp3', 'video.h264'])
    >>> leq_(options, ['-strict', 'experimental', '-vf', 'yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2'])
    >>> leq_(ffmpeg.args, ['ffmpeg', '-y', '-i', 'video.h264', '-i', 'audio.mp3'] + options + ['output.mp4'])
    >>> ffmpeg.kill()
    """
    in_filenames = [f for f in ([in_filenames] if isinstance(in_filenames, string_types) else in_filenames)]
    options = (shlex.split(options) if isinstance(options, string_types) else options) or []

    args = [executable, '-y']
    for in_filename in in_filenames:
        args.extend(['-i', in_filename])
    args.extend(options + [out_filename])
    ffmpeg = Popen(args, stderr=PIPE, close_fds=True)
    if not hasattr(ffmpeg, 'args'):
        ffmpeg.args = args
    make_async(ffmpeg.stderr)
    return ffmpeg, in_filenames, options


def encode(in_filenames, out_filename, options, default_in_duration='00:00:00', time_format='%H:%M:%S', base_track=0,
           ratio_delta=0.01, time_delta=1, max_time_delta=5, sanity_min_ratio=0.95, sanity_max_ratio=1.05,
           encoding='utf-8', executable='ffmpeg'):

    """
    **Example usage**

    >>> from ..filesystem import try_remove

    >>> results = list(encode('small.mp4', 'ff_output.mp4', '-c:a copy -c:v copy'))
    >>> try_remove('ff_output.mp4')
    True
    >>> print(results[-1]['status'])
    SUCCESS

    >>> results = list(encode('small.mp4', 'ff_output.mp4', 'crazy_option'))
    >>> try_remove('ff_output.mp4')
    False
    >>> print(results[-1]['status'])
    ERROR

    >>> results = list(encode({'missing.mp4'}, 'ff_output.mp4', '-c:a copy -c:v copy'))
    >>> try_remove('ff_output.mp4')
    False
    >>> print(results[-1]['status'])
    ERROR
    """

    ffmpeg, in_filenames, options = get_subprocess(in_filenames, out_filename, options, executable=executable)

    # Get input media duration and size to be able to estimate ETA
    in_duration = get_media_duration(in_filenames[base_track]) or str2time(default_in_duration)
    in_size = get_size(in_filenames[base_track])

    # Initialize metrics
    output = ''
    stats = {}
    start_date, start_time = datetime_now(), time.time()
    prev_ratio = prev_time = ratio = 0

    while True:
        # Wait for data to become available
        select.select([ffmpeg.stderr], [], [])
        chunk = ffmpeg.stderr.read()
        if not isinstance(chunk, string_types):
            chunk = chunk.decode(encoding)
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
