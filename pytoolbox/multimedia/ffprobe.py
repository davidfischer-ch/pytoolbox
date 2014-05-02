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

import json, os, re
from datetime import time
from subprocess import check_output
from xml.dom import minidom
from ..datetime import secs_to_time

DURATION_REGEX = re.compile(r'PT(?P<hours>\d+)H(?P<minutes>\d+)M(?P<seconds>[^S]+)S')
WIDTH, HEIGHT = range(2)

MPD_TEST = u"""<?xml version="1.0"?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" mediaPresentationDuration="PT0H6M7.83S">
  <useless text="testing encoding : ça va ou bien ?" />
</MPD>
"""


def get_media_duration(filename):
    u"""
    Returns the duration of a media as an instance of time.

    If input ``filename`` is a MPEG-DASH MPD, then duration will be parser from value of key
    *mediaPresentationDuration*. For any other type of file, this is a *ffprobe* subprocess
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
    >>> print(get_media_duration(u'/tmp/test.mpd').strftime('%H:%M:%S'))
    00:06:10
    >>> os.remove(u'/tmp/test.mpd')
    >>> print(get_media_duration(u'small.mp4').strftime('%H:%M:%S'))
    00:00:05
    """
    if os.path.splitext(filename)[1] == u'.mpd':
        mpd = minidom.parse(filename)
        if mpd.firstChild.nodeName == u'MPD':
            match = DURATION_REGEX.search(mpd.firstChild.getAttribute(u'mediaPresentationDuration'))
            if match is not None:
                seconds = float(match.group(u'seconds'))
                seconds, microseconds = 10, 10
                return time(int(match.group(u'hours')), int(match.group(u'minutes')), seconds, microseconds)
    else:
        infos = get_media_infos(filename)
        duration = secs_to_time(float(infos[u'format'][u'duration'])) if infos else None
        # ffmpeg may return this so strange value, 00:00:00.04, let it being None
        return duration if duration and duration >= time(0, 0, 1) else None
    return None


def get_media_resolution(filename_or_infos=None):
    u"""
    Return [width, height] of the first video stream in ``filename_or_infos`` or None in case of error.

    **Example usage**

    >>> print(get_media_resolution(3.14159265358979323846))
    None
    >>> print(get_media_resolution({}))
    None
    >>> print(get_media_resolution(get_media_infos(u'small.mp4')))
    [560, 320]
    >>> print(get_media_resolution(u'small.mp4'))
    [560, 320]
    >>> print(get_media_resolution(u'small.mp4')[HEIGHT])
    320
    >>> print(get_media_resolution({u'streams': [
    ...     {u'codec_type': u'audio'},
    ...     {u'codec_type': u'video', u'width': u'1920', u'height': u'1080'}
    ... ]}))
    [1920, 1080]
    """
    try:
        if not isinstance(filename_or_infos, dict):
            filename_or_infos = get_media_infos(filename_or_infos)
        first_video_stream = next(s for s in filename_or_infos[u'streams'] if s[u'codec_type'] == u'video')
        return [int(first_video_stream[u'width']), int(first_video_stream[u'height'])]
    except:
        return None


def get_media_infos(filename):
    u"""
    Return a Python dictionary containing informations about the media informations or None in case of error.

    Thanks to: https://gist.github.com/nrk/2286511

    **Example usage**

    >>> from pprint import pprint
    >>> pprint(get_media_infos(u'small.mp4'))  # doctest: +ELLIPSIS
    {u'format': {u'bit_rate': u'551193',
                 u'duration': u'5.568000',
                 u'filename': u'small.mp4',
                 u'format_long_name': u'QuickTime / MOV',
                 u'format_name': u'mov,mp4,m4a,3gp,3g2,mj2',
                 u'nb_programs': 0,
                 u'nb_streams': 2,
                 u'probe_score': 100,
                 u'size': u'383631',
                 u'start_time': u'0.000000',
                 u'tags': {u'compatible_brands': u'mp42isomavc1',
                           u'creation_time': u'2010-03-20 21:29:11',
                           u'encoder': u'HandBrake 0.9.4 2009112300',
                           u'major_brand': u'mp42',
                           u'minor_version': u'0'}},
     u'streams': [{u'avg_frame_rate': u'30/1',
                   u'bit_rate': u'465641',
                   u'codec_long_name': u'H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10',
                   u'codec_name': u'h264',
                   u'codec_tag': u'0x31637661',
                   u'codec_tag_string': u'avc1',
                   u'codec_time_base': u'1/60',
                   u'codec_type': u'video',
                   u'display_aspect_ratio': u'0:1',
                   u'disposition': {u'attached_pic': 0,
                                    u'clean_effects': 0,
                                    u'comment': 0,
                                    u'default': 1,
                                    u'dub': 0,
                                    u'forced': 0,
                                    u'hearing_impaired': 0,
                                    u'karaoke': 0,
                                    u'lyrics': 0,
                                    u'original': 0,
                                    u'visual_impaired': 0},
                   u'duration': u'5.533333',
                   u'duration_ts': 498000,
                   u'has_b_frames': 0,
                   u'height': 320,
                   u'index': 0,
                   u'level': 30,
                   u'nb_frames': u'166',
                   u'pix_fmt': u'yuv420p',
                   u'profile': u'Constrained Baseline',
                   u'r_frame_rate': u'30/1',
                   u'sample_aspect_ratio': u'0:1',
                   u'start_pts': 0,
                   u'start_time': u'0.000000',
                   u'tags': {u'creation_time': u'2010-03-20 21:29:11',
                             u'language': u'und'},
                   u'time_base': u'1/90000',
                   u'width': 560},
                  {u'avg_frame_rate': u'0/0',
                   u'bit_rate': u'83050',
                   u'bits_per_sample': 0,
                   u'channel_layout': u'mono',
                   u'channels': 1,
                   u'codec_long_name': u'AAC (Advanced Audio Coding)',
                   u'codec_name': u'aac',
                   u'codec_tag': u'0x6134706d',
                   u'codec_tag_string': u'mp4a',
                   u'codec_time_base': u'1/48000',
                   u'codec_type': u'audio',
                   u'disposition': {u'attached_pic': 0,
                                    u'clean_effects': 0,
                                    u'comment': 0,
                                    u'default': 1,
                                    u'dub': 0,
                                    u'forced': 0,
                                    u'hearing_impaired': 0,
                                    u'karaoke': 0,
                                    u'lyrics': 0,
                                    u'original': 0,
                                    u'visual_impaired': 0},
                   u'duration': u'5.568000',
                   u'duration_ts': 267264,
                   u'index': 1,
                   u'nb_frames': u'261',
                   u'r_frame_rate': u'0/0',
                   u'sample_fmt': u'fltp',
                   u'sample_rate': u'48000',
                   u'start_pts': 0,
                   u'start_time': u'0.000000',
                   u'tags': {u'creation_time': u'2010-03-20 21:29:11',
                             u'language': u'eng'},
                   u'time_base': u'1/48000'}]}
    """

    try:
        return json.loads(check_output(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format',
                          '-show_streams', filename]))
    except:
        return None
