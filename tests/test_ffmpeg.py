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

from nose.tools import eq_
from pytoolbox.ffmpeg import AUDIO_TRACKS_REGEX, VIDEO_TRACKS_REGEX

INPUT_0 = u"""
ffmpeg version 0.10.11-7:0.10.11-1~saucy1 Copyright (c) 2000-2014 the FFmpeg developers
  built on Feb  6 2014 16:55:15 with gcc 4.8.1
  configuration: --arch=amd64 --disable-stripping --enable-pthreads --enable-runtime-cpudetect
  avcodec     configuration: --arch=amd64 --disable-stripping --enable-pthreads --enable-runtime-cpudetect
  libavutil      51. 35.100 / 51. 35.100
  libavcodec     53. 61.100 / 53. 61.100
  libavformat    53. 32.100 / 53. 32.100
  libavdevice    53.  4.100 / 53.  4.100
  libavfilter     2. 61.100 /  2. 61.100
  libswscale      2.  1.100 /  2.  1.100
  libswresample   0.  6.100 /  0.  6.100
  libpostproc    52.  0.100 / 52.  0.100
Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'project_london_720p_h264.mp4':
  Metadata:
    major_brand     : isom
    minor_version   : 1
    compatible_brands: isomavc1
    creation_time   : 2011-11-05 22:32:44
  Duration: 00:02:44.88, start: 0.000000, bitrate: 2662 kb/s
    Stream #0:0(und): Video: h264 (High) (avc1 / 0x31637661), yuv420p, 1280x720 [SAR 1:1 DAR 16:9], 2504 kb/s, 29.97 fps, 29.97 tbr, 30k tbn, 59.94 tbc
    Metadata:
      creation_time   : 2011-11-05 22:32:44
      handler_name    : GPAC ISO Video Handler
    Stream #0:1(und): Audio: aac (mp4a / 0x6134706D), 44100 Hz, stereo, s16, 155 kb/s
    Metadata:
      creation_time   : 2011-11-05 22:32:45
      handler_name    : GPAC ISO Audio Handler
At least one output file must be specified
"""

INPUT_1 = u"""
ffmpeg version N-54336-g38f1d56 Copyright (c) 2000-2013 the FFmpeg developers
  built on Jul  1 2013 15:15:08 with gcc 4.7 (Ubuntu/Linaro 4.7.3-1ubuntu1)
  configuration: --enable-gpl --enable-libopenjpeg --enable-libmp3lame
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

INPUT_2 = u"""
ffmpeg version 0.10.11-7:0.10.11-1~saucy1 Copyright (c) 2000-2014 the FFmpeg developers
  built on Feb  6 2014 16:55:15 with gcc 4.8.1
  configuration: --arch=amd64 --disable-stripping --extra-version='7:0.10.11-1~saucy1' --prefix=/usr --enable-bzlib
  --extra-version='7:0.10.11-1~saucy1' --libdir=/usr/lib/x86_64-linux-gnu --prefix=/usr --enable-bzlib
  libavutil      51. 35.100 / 51. 35.100
  libavcodec     53. 61.100 / 53. 61.100
  libavformat    53. 32.100 / 53. 32.100
  libavdevice    53.  4.100 / 53.  4.100
  libavfilter     2. 61.100 /  2. 61.100
  libswscale      2.  1.100 /  2.  1.100
  libswresample   0.  6.100 /  0.  6.100
  libpostproc    52.  0.100 / 52.  0.100
[yuv4mpegpipe @ 0x262f300] Estimating duration from bitrate, this may be inaccurate
Input #0, yuv4mpegpipe, from 'temporary/06a12d12-6437-48d5-acc2-c3e099d7d572/v.y4m':
  Duration: N/A, bitrate: N/A
    Stream #0.0: Video: rawvideo (I420 / 0x30323449), yuv420p, 854x480, SAR 1:1 DAR 427:240, 25 fps, 25 tbr, 25 tbn, 25 tbc
At least one output file must be specified
"""

INPUT_3 = u"""
ffmpeg version 2.2.git Copyright (c) 2000-2014 the FFmpeg developers
  built on Mar  3 2014 17:32:03 with gcc 4.8 (Ubuntu/Linaro 4.8.1-10ubuntu9)
  configuration: --prefix=/root/ffmpeg_build --extra-cflags=-I/root/ffmpeg_build/include
  libavutil      52. 66.100 / 52. 66.100
  libavcodec     55. 52.102 / 55. 52.102
  libavformat    55. 33.100 / 55. 33.100
  libavdevice    55. 10.100 / 55. 10.100
  libavfilter     4.  2.100 /  4.  2.100
  libswscale      2.  5.101 /  2.  5.101
  libswresample   0. 18.100 /  0. 18.100
  libpostproc    52.  3.100 / 52.  3.100
Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'big_buck_bunny_1080p_h264.mov':
  Metadata:
    major_brand     : qt
    minor_version   : 537199360
    compatible_brands: qt
    creation_time   : 2008-05-27 18:40:35
    timecode        : 00:00:00:00
  Duration: 00:09:56.46, start: 0.000000, bitrate: 9725 kb/s
    Stream #0:0(eng): Video: h264 (Main) (avc1 / 0x31637661), yuv420p(tv, bt709), 1920x1080, 9282 kb/s, 24 fps, 24 tbr, 2400 tbn, 4800 tbc (default)
    Metadata:
      creation_time   : 2008-05-27 18:40:35
      handler_name    : Apple Alias Data Handler
    Stream #0:1(eng): Data: none (tmcd / 0x64636D74) (default)
    Metadata:
      creation_time   : 2008-05-27 18:40:35
      handler_name    : Apple Alias Data Handler
      timecode        : 00:00:00:00
    Stream #0:2(eng): Audio: aac (mp4a / 0x6134706D), 48000 Hz, 5.1, fltp, 437 kb/s (default)
    Metadata:
      creation_time   : 2008-05-27 18:40:35
      handler_name    : Apple Alias Data Handler
At least one output file must be specified
"""

TEST_TRACKS_REGEXES = (
    (
        INPUT_0,
        (
            {
                u'track': u'0:1', u'codec': u'aac (mp4a / 0x6134706D)', u'sample_format': None,
                u'sample_rate': u'44100', u'channels': u'stereo', u'bit_depth': u'16', u'bitrate': u'155 kb/s'
            },
        ),
        (
            {
                u'track': u'0:0', u'framerate': u'29.97', u'colorimetry': u'yuv420p',
                u'codec': u'h264 (High) (avc1 / 0x31637661)', u'bitrate': u'2504 kb/s',
                u'size': u'1280x720 [SAR 1:1 DAR 16:9]'
            },
        ),
    ),
    (
        INPUT_1,
        (
            {
                u'track': u'0:0', u'codec': u'aac (mp4a / 0x6134706D)', u'sample_format': u'fltp',
                u'sample_rate': u'44100', u'channels': u'stereo', u'bit_depth': None, u'bitrate': u'64 kb/s'
            },
        ),
        None,
    ),
    (
        INPUT_2, None,
        (
            {
                u'track': u'0.0', u'framerate': u'25', u'colorimetry': u'yuv420p',
                u'codec': u'rawvideo (I420 / 0x30323449)', u'bitrate': None, u'size': u'854x480'
            },
        ),
    ),
    (
        INPUT_3,
        (
            {
                u'track': u'0:2', u'codec': u'aac (mp4a / 0x6134706D)', u'sample_format': u'fltp',
                u'sample_rate': u'48000', u'channels': u'5.1', u'bit_depth': None, u'bitrate': u'437 kb/s'
            },
        ),
        (
            {
                u'track': u'0:0', u'framerate': u'24', u'colorimetry': u'yuv420p(tv, bt709)',
                u'codec': u'h264 (Main) (avc1 / 0x31637661)', u'bitrate': u'9282 kb/s',
                u'size': u'1920x1080'
            },
        ),
    ),
)


class TestFFmpeg(object):

    def test_encoding_regex(self):
        for input_string, audio_tracks, video_tracks in TEST_TRACKS_REGEXES:
            for index, match in enumerate(VIDEO_TRACKS_REGEX.finditer(input_string)):
                eq_(match.groupdict(), video_tracks[index])
            for index, match in enumerate(AUDIO_TRACKS_REGEX.finditer(input_string)):
                eq_(match.groupdict(), audio_tracks[index])
