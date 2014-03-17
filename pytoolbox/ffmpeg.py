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
from .datetime import datetime_now, time_ratio, total_seconds
from .encoding import string_types, to_bytes
from .filesystem import get_size
from .subprocess import make_async


AUDIO_TRACKS_REGEX = re.compile(
    ur'Stream #(?P<track>\d+.\d+)[^\d]*:\s+Audio:\s+(?P<codec>[^,]+),\s+(?P<sample_rate>\d+) Hz,\s+'
    ur'(?P<channels>[^,]+),\s+(s(?P<bit_depth>\d+)|(?P<sample_format>[^,]+)),\s+(?P<bitrate>[^,]+/s)')

VIDEO_TRACKS_REGEX = re.compile(
    ur'Stream #(?P<track>\d+.\d+)[^\d]*:\s+Video:\s+(?P<codec>[^,]+),\s+(?P<colorimetry>.+),\s+'
    ur'(?P<size>\d+x\d+[^,]+),\s+(?P<bitrate>[^,]+/s)?[^,]*,\s+(?P<framerate>\S+)\s+fps,')

DURATION_REGEX = re.compile(r'PT(?P<hours>\d+)H(?P<minutes>\d+)M(?P<seconds>[^S]+)S')
SIZE_REGEX = re.compile(ur'(?P<width>[0-9]+)x(?P<height>[0-9]+).*')
WIDTH, HEIGHT = range(2)  # The indexes of the width and the height in size [width, height]

# frame= 2071 fps=  0 q=-1.0 size=   34623kB time=00:01:25.89 bitrate=3302.3kbits/s
ENCODING_REGEX = re.compile(
    r'frame=\s*(?P<frame>\d+)\s+fps=\s*(?P<fps>\d+)\s+q=\s*(?P<q>\S+)\s+\S*size=\s*(?P<size>\S+)\s+'
    r'time=\s*(?P<time>\S+)\s+bitrate=\s*(?P<bitrate>\S+)')

MPD_TEST = u"""<?xml version="1.0"?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" mediaPresentationDuration="PT0H6M7.83S">
  <useless text="testing encoding : ça va ou bien ?" />
</MPD>
"""


def get_media_duration(filename):
    u"""
    Returns the duration of a media as a string.

    If input ``filename`` is a MPEG-DASH MPD, then duration will be parser from value of key
    *mediaPresentationDuration*. For any other type of file, this is a *ffmpeg* subprocess
    that detect duration of the media.

    **Example usage**

    >>> from codecs import open
    >>> with open(u'/tmp/test.txt', u'w', encoding=u'utf-8') as f:
    ...     f.write(u'Hey, I am not a MPD nor a média')
    >>> print(get_media_duration(u'/tmp/test.txt'))
    None
    >>> os.remove(u'/tmp/test.txt')
    >>> with open(u'/tmp/test.mpd', u'w', encoding=u'utf-8') as f:
    ...     f.write(MPD_TEST)
    >>> print(get_media_duration(u'/tmp/test.mpd'))
    00:06:07.83
    >>> os.remove(u'/tmp/test.mpd')
    >>> print(get_media_duration(u'small.mp4'))
    00:00:05.56
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
        match = re.search(ur'Duration: (?P<duration>[\d:\.]+),', unicode(pipe.stderr.read()))
        if not match:
            return None
        duration = match.group(u'duration')
        # ffmpeg may return this so strange value, 00:00:00.04, let it being None
        return duration if duration and duration != u'00:00:00.04' else None
    return None


def get_media_resolution(filename_or_tracks=None):
    u"""
    Return [width, height] of the first video track in ``filename_or_tracks`` or None.

    **Example usage**

    >>> print(get_media_resolution(get_media_tracks(u'small.mp4')))
    [560, 320]
    >>> print(get_media_resolution(u'small.mp4'))
    [560, 320]
    >>> print(get_media_resolution(u'small.mp4')[HEIGHT])
    320
    >>> print(get_media_resolution({u'video': {u'0:0': {u'size': u'1920x1080 [SAR 1:1 DAR 16:9]'}}}))
    [1920, 1080]
    """
    try:
        if not isinstance(filename_or_tracks, dict):
            filename_or_tracks = get_media_tracks(filename_or_tracks)
        first_video_track = next(filename_or_tracks[u'video'].itervalues())[u'size']
        match = SIZE_REGEX.search(first_video_track)
        if not match:
            return None
        return [int(match.group(u'width')), int(match.group(u'height'))]
    except:
        return None


def get_media_tracks(filename):
    u"""
    Return a Python dictionary containing informations about the media tracks or None in case of error.

    .. warning:: FIXME Add unit-test to update REGEX by mocking ffmpeg with TEST_VECTOR and checking the output !

    **Example usage**

    Remark: In some systems the tracks are numbered with a dot (0.1) and sometimes with a : (0:1).

    >>> from pprint import pprint
    >>> pprint(get_media_tracks(u'small.mp4'))  # doctest: +ELLIPSIS
    {u'audio': {'0...1': {u'bit_depth': '16',
                        u'bitrate': '83 kb/s',
                        u'channels': 'mono',
                        u'codec': 'aac...',
                        u'sample_format': u'fixed',
                        u'sample_rate': '48000'}},
     u'duration': u'00:00:05.56',
     u'video': {'0...0': {u'bitrate': '465 kb/s',
                        u'codec': 'h264 (Constrained Baseline)...',
                        u'colorimetry': 'yuv420p',
                        u'estimated_frames': 166,
                        u'framerate': '30',
                        u'size': '560x320'}}}
    """
    duration = get_media_duration(filename)
    duration_secs = total_seconds(duration) if duration else 0
    cmd = u'ffmpeg -i "{0}"'.format(filename)
    pipe = Popen(shlex.split(cmd), stderr=PIPE, close_fds=True)
    output = pipe.stderr.read()
    audio, video = {}, {}
    for match in AUDIO_TRACKS_REGEX.finditer(output):
        group = match.groupdict()
        track = group.pop(u'track')
        group[u'sample_format'] = group[u'sample_format'] or u'fixed'
        audio[track] = group
    for match in VIDEO_TRACKS_REGEX.finditer(output):
        group = match.groupdict()
        track = group.pop(u'track')
        group[u'estimated_frames'] = int(float(group[u'framerate']) * duration_secs)
        video[track] = group
    return {u'duration': duration, u'audio': audio, u'video': video}


def encode(in_filenames, out_filename, encoder_string, default_in_duration=u'00:00:00', base_track=0, ratio_delta=0.01,
           time_delta=1, max_time_delta=5, sanity_min_ratio=0.95, sanity_max_ratio=1.05):

    if isinstance(in_filenames, string_types):
        in_filenames = [in_filenames]

    # Get input media duration and size to be able to estimate ETA
    in_duration = get_media_duration(in_filenames[base_track]) or default_in_duration
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
            out_duration = stats[u'time']
            ratio = time_ratio(out_duration, in_duration)
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
    ratio = time_ratio(out_duration, in_duration) if out_duration else 0.0
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
