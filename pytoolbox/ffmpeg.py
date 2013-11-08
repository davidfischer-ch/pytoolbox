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

import os, re, select, shlex, time
from subprocess import Popen, PIPE
from xml.dom import minidom
from .datetime import datetime_now, total_seconds
from .encoding import to_bytes
from .filesystem import get_size
from .subprocess import make_async


AUDIO_TRACKS_REGEX = re.compile(
    ur'Stream #(?P<track>\d+.\d+)\s*\S+ Audio:\s+(?P<codec>[^,]+),\s+(?P<sample_rate>\d+) Hz,\s+'
    ur'(?P<channels>[^,]+),\s+s(?P<bit_depth>\d+),\s+(?P<bitrate>[^,]+/s)')

VIDEO_TRACKS_REGEX = re.compile(
    ur'Stream #(?P<track>\d+.\d+)\s*\S+ Video:\s+(?P<codec>[^,]+),\s+(?P<colorimetry>[^,]+),\s+'
    ur'(?P<size>[^,]+),\s+(?P<bitrate>[^,]+/s),\s+(?P<framerate>\S+)\s+fps,')

DURATION_REGEX = re.compile(r'PT(?P<hours>\d+)H(?P<minutes>\d+)M(?P<seconds>[^S]+)S')

# frame= 2071 fps=  0 q=-1.0 size=   34623kB time=00:01:25.89 bitrate=3302.3kbits/s
ENCODING_REGEX = re.compile(
    r'frame=\s*(?P<frame>\d+)\s+fps=\s*(?P<fps>\d+)\s+q=\s*(?P<q>\S+)\s+\S*size=\s*(?P<size>\S+)\s+'
    r'time=\s*(?P<time>\S+)\s+bitrate=\s*(?P<bitrate>\S+)')

MPD_TEST = u"""<?xml version="1.0"?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" mediaPresentationDuration="PT0H6M7.83S">
  <useless text="testing encoding : ça va ou bien ?" />
</MPD>
"""

TEST_VECTOR = u"""
ffmpeg version N-54336-g38f1d56 Copyright (c) 2000-2013 the FFmpeg developers
  built on Jul  1 2013 15:15:08 with gcc 4.7 (Ubuntu/Linaro 4.7.3-1ubuntu1)
  configuration: --enable-gpl --enable-libx264 --disable-yasm --enable-libvo-aacenc --enable-version3 --enable-opencl --enable-libopenjpeg --enable-libmp3lame
  libavutil      52. 38.100 / 52. 38.100
  libavcodec     55. 18.100 / 55. 18.100
  libavformat    55. 10.100 / 55. 10.100
  libavdevice    55.  2.100 / 55.  2.100
  libavfilter     3. 77.101 /  3. 77.101
  libswscale      2.  3.100 /  2.  3.100
  libswresample   0. 17.102 /  0. 17.102
  libpostproc    52.  3.100 / 52.  3.100
Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'test.m4a':
  Metadata:
    major_brand     : M4A
    minor_version   : 512
    compatible_brands: isomiso2
    title           : Donjon de Naheulbeuk 01
    artist          : Aventures
    album           : Donjon de Naheulbeuk
    date            : 2008
    encoder         : Lavf55.10.100
    genre           : Aventures
    track           : 1
  Duration: 00:03:46.01, start: 0.000000, bitrate: 65 kb/s
    Stream #0:0(und): Audio: aac (mp4a / 0x6134706D), 44100 Hz, stereo, fltp, 64 kb/s
    Metadata:
      handler_name    : SoundHandler
At least one output file must be specified
"""

def get_media_duration(filename):
    u"""
    Returns the duration of a media as a string.

    If input ``filename`` is a MPEG-DASH MPD, then duration will be parser from value of key
    *mediaPresentationDuration*. For any other type of file, this is a *ffmpeg* subprocess
    that detect duration of the media.

    **Example usage**

    >>> from codecs import open
    >>> open(u'/tmp/test.txt', u'w', encoding=u'utf-8').write(u'Hey, I am not a MPD nor a média')
    >>> print(get_media_duration(u'/tmp/test.txt'))
    None
    >>> os.remove(u'/tmp/test.txt')
    >>> open(u'/tmp/test.mpd', u'w', encoding=u'utf-8').write(MPD_TEST)
    >>> print(get_media_duration(u'/tmp/test.mpd'))
    00:06:07.83
    >>> os.remove(u'/tmp/test.mpd')
    >>>
    >> print(get_media_duration(u'test.mp4'))
    01:45:23.62
    """
    if os.path.splitext(filename)[1] == u'.mpd':
        mpd = minidom.parse(filename)
        if mpd.firstChild.nodeName == u'MPD':
            match = DURATION_REGEX.search(mpd.firstChild.getAttribute(u'mediaPresentationDuration'))
            if match is not None:
                return u'{0:02d}:{1:02d}:{2:05.2f}'.format(
                    int(match.group(u'hours')), int(match.group(u'minutes')),
                    float(match.group(u'seconds')))
    else:
        cmd = u'ffmpeg -i "{0}"'.format(filename)
        pipe = Popen(shlex.split(to_bytes(cmd)), stderr=PIPE, close_fds=True)
        match = re.search(ur'Duration: (?P<duration>\S+),', unicode(pipe.stderr.read()))
        if not match:
            return None
        duration = match.group(u'duration')
        # ffmpeg may return this so strange value, 00:00:00.04, let it being None
        return duration if duration and duration != u'00:00:00.04' else None
    return None


def get_media_tracks(filename):
    u"""

    .. warning:: FIXME Add unit-test to update REGEX by mocking ffmpeg with TEST_VECTOR and checking the output !

    **Example usage**

    ::
        >> from pytoolbox.ffmpeg import get_media_tracks
        >> pprint(get_media_tracks('test.mp4')
        {
            'audio': {
                '0.1': {
                    'bit_depth': '16', 'bitrate': '155 kb/s', 'channels': 'stereo', 'codec': 'aac',
                    'sample_rate': '44100'
                }
            },
            'duration': '00:02:44.88',
            'video': {
                '0.0': {
                    'bitrate': '2504 kb/s', 'codec': 'h264 (High)', 'colorimetry': 'yuv420p', 'estimated_frames': 4941,
                    'framerate': '29.97', 'size': '1280x720 [PAR 1:1 DAR 16:9]'
                }
            }
        }

    """
    duration = get_media_duration(filename)
    if not duration:
        return None
    duration_secs = total_seconds(duration)
    cmd = u'ffmpeg -i "{0}"'.format(filename)
    pipe = Popen(shlex.split(cmd), stderr=PIPE, close_fds=True)
    output = pipe.stderr.read()
    audio, video = {}, {}
    for match in AUDIO_TRACKS_REGEX.finditer(output):
        group = match.groupdict()
        track = group.pop(u'track')
        audio[track] = group
    for match in VIDEO_TRACKS_REGEX.finditer(output):
        group = match.groupdict()
        track = group.pop(u'track')
        group[u'estimated_frames'] = int(float(group[u'framerate']) * duration_secs)
        video[track] = group
    return {u'duration': duration, u'audio': audio, u'video': video}


def encode(in_filename, out_filename, encoder_string, ratio_delta=0.01, time_delta=1, max_time_delta=5,
           sanity_min_ratio=0.95, sanity_max_ratio=1.05):

    def get_ratio(in_duration, out_duration):
        try:
            ratio = total_seconds(out_duration) / total_seconds(in_duration)
            return 0.0 if ratio < 0.0 else 1.0 if ratio > 1.0 else ratio
        except ZeroDivisionError:
            return 1.0

   # Get input media duration and size to be able to estimate ETA
    in_duration, in_size = get_media_duration(in_filename), get_size(in_filename)

    # Initialize metrics
    output = u''
    stats = {}
    start_date, start_time = datetime_now(), time.time()
    prev_ratio = prev_time = ratio = 0

    # Create FFmpeg subprocess
    cmd = u'ffmpeg -y -i "{0}" {1} "{2}"'.format(in_filename, encoder_string, out_filename)
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
            out_duration = stats[u'time']
            ratio = get_ratio(in_duration, out_duration)
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
                    u'in_duration': in_duration,
                    u'out_size': get_size(out_filename),
                    u'out_duration': out_duration,
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
    ratio = get_ratio(in_duration, out_duration)
    yield {
        u'status': u'ERROR' if returncode else u'SUCCESS',
        u'output': output,
        u'returncode': returncode,
        u'start_date': start_date,
        u'elapsed_time': elapsed_time,
        u'eta_time': 0,
        u'in_size': in_size,
        u'in_duration': in_duration,
        u'out_size': get_size(out_filename),
        u'out_duration': out_duration,
        u'percent': int(100 * ratio) if returncode else 100,  # Assume that a successful encoding = 100%
        u'frame': stats.get(u'frame'),
        u'fps': stats.get(u'fps'),
        u'bitrate': stats.get(u'bitrate'),
        u'quality': stats.get(u'q'),
        u'sanity': sanity_min_ratio <= ratio <= sanity_max_ratio
    }
