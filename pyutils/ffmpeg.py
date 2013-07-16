#!/usr/bin/env python
# -*- coding: utf-8 -*-

#**************************************************************************************************#
#                               PYUTILS - SOME PYTHON UTILITY FUNCTIONS
#
#   Description : Toolbox for Python scripts
#   Authors     : David Fischer
#   Contact     : david.fischer.ch@gmail.com
#   Copyright   : 2013-2013 David Fischer. All rights reserved.
#**************************************************************************************************#
#
#  This file is part of pyutils.
#
#  This project is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with this project.
#  If not, see <http://www.gnu.org/licenses/>
#
#  Retrieved from git clone https://github.com/davidfischer-ch/pyutils.git

import fcntl, os, re, select, shlex, subprocess, time
from xml.dom import minidom
from pyutils import duration2secs

AUDIO_TRACKS_REGEX = re.compile(
    r'Stream #(?P<track>\d+.\d+)\S+ Audio:\s+(?P<codec>[^,]+),\s+(?P<sample_rate>\d+) Hz,\s+'
    r'(?P<channels>[^,]+),\s+s(?P<bit_depth>\d+),\s+(?P<bitrate>[^,]+/s)')

VIDEO_TRACKS_REGEX = re.compile(
    r'Stream #(?P<track>\d+.\d+)\S+ Video:\s+(?P<codec>[^,]+),\s+(?P<colorimetry>[^,]+),\s+'
    r'(?P<size>[^,]+),\s+(?P<bitrate>[^,]+/s),\s+(?P<framerate>\S+)\s+fps,')

DURATION_REGEX = re.compile(r'PT(?P<hours>\d+)H(?P<minutes>\d+)M(?P<seconds>[^S]+)S')

MPD_TEST = """<?xml version="1.0"?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" mediaPresentationDuration="PT0H6M7.83S">
</MPD>
"""


def get_media_duration(filename):
    u"""
    Returns the duration of a media as a string.

    If input ``filename`` is a MPEG-DASH MPD, then duration will be parser from value of key
    *mediaPresentationDuration*. For any other type of file, this is a *ffmpeg* subprocess
    that detect duration of the media.

    **Example usage**:

    >>> import os
    >>> print(get_media_duration('ffmpeg.py'))
    None
    >>> open('/tmp/test.mpd', 'w').write(MPD_TEST)
    >>> print(get_media_duration('/tmp/test.mpd'))
    00:06:07.83
    >>> os.remove('/tmp/test.mpd')

    >> print(get_media_duration('test.mp4'))
    01:45:23.62
    """
    if os.path.splitext(filename)[1] == '.mpd':
        mpd = minidom.parse(filename)
        if mpd.firstChild.nodeName == 'MPD':
            match = DURATION_REGEX.search(mpd.firstChild.getAttribute('mediaPresentationDuration'))
            if match is not None:
                return '%02d:%02d:%05.2f' % (int(match.group('hours')), int(match.group('minutes')),
                                             float(match.group('seconds')))
    else:
        cmd = 'ffmpeg -i "%s"' % filename
        pipe = subprocess.Popen(shlex.split(cmd), stderr=subprocess.PIPE, close_fds=True)
        duration = re.search(r'Duration: (?P<duration>\S+),', pipe.stderr.read())
        return None if not duration else duration.group('duration')
    return None


def get_media_tracks(filename):
    u"""
    **Example usage**:

    >> from pyutils.ffmpeg import get_media_tracks
    >> pprint(get_media_tracks('test.mp4')
    {'audio': {'0.1': {'bit_depth': '16',
                       'bitrate': '155 kb/s',
                       'channels': 'stereo',
                       'codec': 'aac',
                       'sample_rate': '44100'}},
     'duration': '00:02:44.88',
     'video': {'0.0': {'bitrate': '2504 kb/s',
                       'codec': 'h264 (High)',
                       'colorimetry': 'yuv420p',
                       'estimated_frames': 4941,
                       'framerate': '29.97',
                       'size': '1280x720 [PAR 1:1 DAR 16:9]'}}}
    """
    duration = get_media_duration(filename)
    if not duration:
        return None
    duration_secs = duration2secs(duration)
    cmd = 'ffmpeg -i "%s"' % filename
    pipe = subprocess.Popen(shlex.split(cmd), stderr=subprocess.PIPE, close_fds=True)
    output = pipe.stderr.read()
    audio, video = {}, {}
    for match in AUDIO_TRACKS_REGEX.finditer(output):
        group = match.groupdict()
        track = group.pop('track')
        audio[track] = group
    for match in VIDEO_TRACKS_REGEX.finditer(output):
        group = match.groupdict()
        track = group.pop('track')
        group['estimated_frames'] = int(float(group['framerate']) * duration_secs)
        video[track] = group
    return {'duration': duration, 'audio': audio, 'video': video}


def encode(in_filename, out_filename, encoder_string, overwrite, sleep_time=1, callback=None):
    if os.path.exists(out_filename):
        if not overwrite:
            return False
        os.unlink(out_filename)
    cmd = 'ffmpeg -i "%s" ' + encoder_string + ' "%s"' % (in_filename, out_filename)
    pipe = subprocess.Popen(shlex.split(cmd), stderr=subprocess.PIPE, close_fds=True)

    # http://stackoverflow.com/questions/1388753/how-to-get-output-from-subprocess-popen
    fcntl.fcntl(pipe.stderr.fileno(), fcntl.F_SETFL,
                fcntl.fcntl(pipe.stderr.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK,)

    # frame= 2071 fps=  0 q=-1.0 size=   34623kB time=00:01:25.89 bitrate=3302.3kbits/s
    regex = re.compile(
        r'frame=\s*(?P<frame>\d+)\s+fps=\s*(?P<fps>\d+)\s+q=\s*(?P<q>\S+)\s+\S*'
        r'size=\s*(?P<size>\S+)\s+time=\s*(?P<time>\S+)\s+bitrate=\s*(?P<bitrate>\S+)')
    while True:
        readx = select.select([pipe.stderr.fileno()], [], [])[0]
        if readx:
            chunk = pipe.stderr.read()
            if chunk == '':
                break
            match = regex.match(chunk)
            if match and callback:
                callback(match.groupdict())
        time.sleep(sleep_time)
    return True

#def test_callback(dict):
#    print dict
#
#if __name__ == '__main__':
#    print FFmpeg.duration(movie)
#    FFmpeg.encode(movie, movie_out, '-acodec copy -vcodec copy', True, test_callback)

# Main ---------------------------------------------------------------------------------------------

if __name__ == '__main__':
    print('Test ffmpeg with doctest')
    import doctest
    assert(doctest.testmod(verbose=True).failed == 0)
    print('OK')
