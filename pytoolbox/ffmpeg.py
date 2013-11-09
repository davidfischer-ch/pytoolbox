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

import fcntl, os, re, select, shlex, subprocess, time
from xml.dom import minidom
from .datetime import total_seconds
from .encoding import to_bytes


AUDIO_TRACKS_REGEX = re.compile(
    ur'Stream #(?P<track>\d+.\d+)\S+ Audio:\s+(?P<codec>[^,]+),\s+(?P<sample_rate>\d+) Hz,\s+'
    ur'(?P<channels>[^,]+),\s+s(?P<bit_depth>\d+),\s+(?P<bitrate>[^,]+/s)')

VIDEO_TRACKS_REGEX = re.compile(
    ur'Stream #(?P<track>\d+.\d+)\S+ Video:\s+(?P<codec>[^,]+),\s+(?P<colorimetry>[^,]+),\s+'
    ur'(?P<size>[^,]+),\s+(?P<bitrate>[^,]+/s),\s+(?P<framerate>\S+)\s+fps,')

DURATION_REGEX = re.compile(r'PT(?P<hours>\d+)H(?P<minutes>\d+)M(?P<seconds>[^S]+)S')

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
        pipe = subprocess.Popen(shlex.split(to_bytes(cmd)), stderr=subprocess.PIPE, close_fds=True)
        match = re.search(ur'Duration: (?P<duration>\S+),', unicode(pipe.stderr.read()))
        if not match:
            return None
        duration = match.group(u'duration')
        # ffmpeg may return this so strange value, 00:00:00.04, let it being None
        return duration if duration and duration != u'00:00:00.04' else None
    return None


def get_media_tracks(filename):
    u"""
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
    pipe = subprocess.Popen(shlex.split(cmd), stderr=subprocess.PIPE, close_fds=True)
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


def encode(in_filename, out_filename, encoder_string, overwrite, sleep_time=1, callback=None):
    if os.path.exists(out_filename):
        if not overwrite:
            return False
        os.unlink(out_filename)
    cmd = u'ffmpeg -i "{0}" {1} "{2}"'.format(in_filename, encoder_string, out_filename)
    pipe = subprocess.Popen(shlex.split(cmd), stderr=subprocess.PIPE, close_fds=True)

    # http://stackoverflow.com/questions/1388753/how-to-get-output-from-subprocess-popen
    fcntl.fcntl(pipe.stderr.fileno(), fcntl.F_SETFL,
                fcntl.fcntl(pipe.stderr.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK,)

    # frame= 2071 fps=  0 q=-1.0 size=   34623kB time=00:01:25.89 bitrate=3302.3kbits/s
    regex = re.compile(
        ur'frame=\s*(?P<frame>\d+)\s+fps=\s*(?P<fps>\d+)\s+q=\s*(?P<q>\S+)\s+\S*'
        ur'size=\s*(?P<size>\S+)\s+time=\s*(?P<time>\S+)\s+bitrate=\s*(?P<bitrate>\S+)')
    while True:
        readx = select.select([pipe.stderr.fileno()], [], [])[0]
        if readx:
            chunk = pipe.stderr.read()
            if chunk == u'':
                break
            match = regex.match(chunk)
            if match and callback:
                callback(match.groupdict())
        time.sleep(sleep_time)
    return True

#def test_callback(dict):
#    print(dict)
#
#if __name__ == '__main__':
#    print(FFmpeg.duration(movie))
#    FFmpeg.encode(movie, movie_out, '-acodec copy -vcodec copy', True, test_callback)
