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

import json, os, re
from datetime import time
from subprocess import check_output
from xml.dom import minidom
from ..datetime import secs_to_time

DURATION_REGEX = re.compile(r'PT(?P<hours>\d+)H(?P<minutes>\d+)M(?P<seconds>[^S]+)S')
WIDTH, HEIGHT = range(2)

MPD_TEST = """<?xml version="1.0"?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" mediaPresentationDuration="PT0H6M7.83S">
  <useless text="testing encoding : ça va ou bien ?" />
</MPD>
"""


def get_media_duration(filename_or_infos):
    """
    Returns the duration of a media as an instance of time or None in case of error.

    If input ``filename`` is a MPEG-DASH MPD, then duration will be parser from value of key
    *mediaPresentationDuration*. For any other type of file, this is a *ffprobe* subprocess
    that detect duration of the media.

    **Example usage**

    >>> from codecs import open

    Bad file format:

    >>> with open('/tmp/test.txt', 'w', encoding='utf-8') as f:
    ...     f.write('Hey, I am not a MPD nor a média')
    >>> print(get_media_duration('/tmp/test.txt'))
    None
    >>> os.remove('/tmp/test.txt')

    Some random bad things:

    >>> print(get_media_duration({}))
    None

    A MPEG-DASH MPD:

    >>> with open('/tmp/test.mpd', 'w', encoding='utf-8') as f:
    ...     f.write(MPD_TEST)
    >>> print(get_media_duration('/tmp/test.mpd').strftime('%H:%M:%S'))
    00:06:10
    >>> os.remove('/tmp/test.mpd')

    A MP4:

    >>> print(get_media_duration('small.mp4').strftime('%H:%M:%S'))
    00:00:05
    >>> print(get_media_duration(get_media_infos('small.mp4')).strftime('%H:%M:%S'))
    00:00:05
    """
    is_filename = not isinstance(filename_or_infos, dict)
    if is_filename and os.path.splitext(filename_or_infos)[1] == '.mpd':
        mpd = minidom.parse(filename_or_infos)
        if mpd.firstChild.nodeName == 'MPD':
            match = DURATION_REGEX.search(mpd.firstChild.getAttribute('mediaPresentationDuration'))
            if match is not None:
                seconds = float(match.group('seconds'))
                seconds, microseconds = 10, 10
                return time(int(match.group('hours')), int(match.group('minutes')), seconds, microseconds)
    else:
        infos = get_media_infos(filename_or_infos) if is_filename else filename_or_infos
        try:
            duration = secs_to_time(float(infos['format']['duration'])) if infos else None
        except KeyError:
            return None
        # ffmpeg may return this so strange value, 00:00:00.04, let it being None
        return duration if duration and duration >= time(0, 0, 1) else None
    return None


def get_media_resolution(filename_or_infos):
    """
    Return [width, height] of the first video stream in ``filename_or_infos`` or None in case of error.

    **Example usage**

    >>> print(get_media_resolution(3.14159265358979323846))
    None
    >>> print(get_media_resolution({}))
    None
    >>> print(get_media_resolution(get_media_infos('small.mp4')))
    [560, 320]
    >>> print(get_media_resolution('small.mp4'))
    [560, 320]
    >>> print(get_media_resolution('small.mp4')[HEIGHT])
    320
    >>> print(get_media_resolution({'streams': [
    ...     {'codec_type': 'audio'},
    ...     {'codec_type': 'video', 'width': '1920', 'height': '1080'}
    ... ]}))
    [1920, 1080]
    """
    if not isinstance(filename_or_infos, dict):
        filename_or_infos = get_media_infos(filename_or_infos)
    try:
        first_video_stream = next(s for s in filename_or_infos['streams'] if s['codec_type'] == 'video')
        return [int(first_video_stream['width']), int(first_video_stream['height'])]
    except:
        return None


def get_media_infos(filename):
    """
    Return a Python dictionary containing informations about the media informations or None in case of error.

    Thanks to: https://gist.github.com/nrk/2286511

    **Example usage**

    Remark: This doctest is disabled because in Travis CI, the installed ffprobe doesn't output the same exact string.

    >> from pprint import pprint
    >> pprint(get_media_infos('small.mp4'))  # doctest: +ELLIPSIS
    {'format': {'bit_rate': '551193',
                 'duration': '5.568000',
                 'filename': 'small.mp4',
                 'format_long_name': 'QuickTime / MOV',
                 'format_name': 'mov,mp4,m4a,3gp,3g2,mj2',
                 'nb_programs': 0,
                 'nb_streams': 2,
                 'probe_score': 100,
                 'size': '383631',
                 'start_time': '0.000000',
                 'tags': {'compatible_brands': 'mp42isomavc1',
                          'creation_time': '2010-03-20 21:29:11',
                          'encoder': 'HandBrake 0.9.4 2009112300',
                          'major_brand': 'mp42',
                          'minor_version': '0'}},
     'streams': [{'avg_frame_rate': '30/1',
                   'bit_rate': '465641',
                   'codec_long_name': 'H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10',
                   'codec_name': 'h264',
                   'codec_tag': '0x31637661',
                   'codec_tag_string': 'avc1',
                   'codec_time_base': '1/60',
                   'codec_type': 'video',
                   'display_aspect_ratio': '0:1',
                   'disposition': {'attached_pic': 0,
                                   'clean_effects': 0,
                                   'comment': 0,
                                   'default': 1,
                                   'dub': 0,
                                   'forced': 0,
                                   'hearing_impaired': 0,
                                   'karaoke': 0,
                                   'lyrics': 0,
                                   'original': 0,
                                   'visual_impaired': 0},
                   'duration': '5.533333',
                   'duration_ts': 498000,
                   'has_b_frames': 0,
                   'height': 320,
                   'index': 0,
                   'level': 30,
                   'nb_frames': '166',
                   'pix_fmt': 'yuv420p',
                   'profile': 'Constrained Baseline',
                   'r_frame_rate': '30/1',
                   'sample_aspect_ratio': '0:1',
                   'start_pts': 0,
                   'start_time': '0.000000',
                   'tags': {'creation_time': '2010-03-20 21:29:11',
                            'language': 'und'},
                   'time_base': '1/90000',
                   'width': 560},
                  {'avg_frame_rate': '0/0',
                   'bit_rate': '83050',
                   'bits_per_sample': 0,
                   'channel_layout': 'mono',
                   'channels': 1,
                   'codec_long_name': 'AAC (Advanced Audio Coding)',
                   'codec_name': 'aac',
                   'codec_tag': '0x6134706d',
                   'codec_tag_string': 'mp4a',
                   'codec_time_base': '1/48000',
                   'codec_type': 'audio',
                   'disposition': {'attached_pic': 0,
                                   'clean_effects': 0,
                                   'comment': 0,
                                   'default': 1,
                                   'dub': 0,
                                   'forced': 0,
                                   'hearing_impaired': 0,
                                   'karaoke': 0,
                                   'lyrics': 0,
                                   'original': 0,
                                   'visual_impaired': 0},
                   'duration': '5.568000',
                   'duration_ts': 267264,
                   'index': 1,
                   'nb_frames': '261',
                   'r_frame_rate': '0/0',
                   'sample_fmt': 'fltp',
                   'sample_rate': '48000',
                   'start_pts': 0,
                   'start_time': '0.000000',
                   'tags': {'creation_time': '2010-03-20 21:29:11',
                             'language': 'eng'},
                   'time_base': '1/48000'}]}
    """

    try:
        return json.loads(check_output(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format',
                          '-show_streams', filename]))
    except:
        return None
