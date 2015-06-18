# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2015 David Fischer. All rights reserved.
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

import datetime, os, tempfile, unittest
from codecs import open
from os.path import isfile, join
from pytoolbox.filesystem import try_remove
from pytoolbox.multimedia import ffmpeg
from pytoolbox.multimedia.ffmpeg import (
    to_bit_rate, to_frame_rate, to_size, AudioStream, EncodeState, Format, Media, VideoStream, HEIGHT
)
from pytoolbox.unittest import FilterByTagsMixin

MPD_TEST = """<?xml version="1.0"?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" mediaPresentationDuration="PT0H6M7.83S">
  <useless text="testing encoding : ça va ou bien ?" />
</MPD>
"""
STATIC_FFMPEG_BINARY = join(tempfile.gettempdir(), 'ffmpeg')
STATIC_FFPROBE_BINARY = join(tempfile.gettempdir(), 'ffprobe')
WITH_FFMPEG = isfile(STATIC_FFMPEG_BINARY)
MEDIA_INFOS = {
    'format': {
        'bit_rate': '551193',
        'duration': '5.568000',
        'filename': 'small.mp4',
        'format_long_name': 'QuickTime / MOV',
        'format_name': 'mov,mp4,m4a,3gp,3g2,mj2',
        'nb_programs': 0,
        'nb_streams': 2,
        'probe_score': 100,
        'size': '383631',
        'start_time': '0.000000',
        'tags': {
            'compatible_brands': 'mp42isomavc1',
            'creation_time': '2010-03-20 21:29:11',
            'encoder': 'HandBrake 0.9.4 2009112300',
            'major_brand': 'mp42',
            'minor_version': '0'
        }
    },
    'streams': [
        {
            'avg_frame_rate': '30/1',
            'bit_rate': '465641',
            'codec_long_name': 'H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10',
            'codec_name': 'h264',
            'codec_tag': '0x31637661',
            'codec_tag_string': 'avc1',
            'codec_time_base': '1/60',
            'codec_type': 'video',
            'display_aspect_ratio': '0:1',
            'disposition': {
                'attached_pic': 0,
                'clean_effects': 0,
                'comment': 0,
                'default': 1,
                'dub': 0,
                'forced': 0,
                'hearing_impaired': 0,
                'karaoke': 0,
                'lyrics': 0,
                'original': 0,
                'visual_impaired': 0
            },
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
            'tags': {
                'creation_time': '2010-03-20 21:29:11',
                'language': 'und'
            },
            'time_base': '1/90000',
            'width': 560
        },
        {
            'avg_frame_rate': '0/0',
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
            'disposition': {
                'attached_pic': 0,
                'clean_effects': 0,
                'comment': 0,
                'default': 1,
                'dub': 0,
                'forced': 0,
                'hearing_impaired': 0,
                'karaoke': 0,
                'lyrics': 0,
                'original': 0,
                'visual_impaired': 0
            },
            'duration': '5.568000',
            'duration_ts': 267264,
            'index': 1,
            'nb_frames': '261',
            'r_frame_rate': '0/0',
            'sample_fmt': 'fltp',
            'sample_rate': '48000',
            'start_pts': 0,
            'start_time': '0.000000',
            'tags': {
                'creation_time': '2010-03-20 21:29:11',
                'language': 'eng'
            },
            'time_base': '1/48000'
        }
    ]
}


class MockFFmpeg(ffmpeg.FFmpeg):

    executable = STATIC_FFMPEG_BINARY


class MockFFprobe(ffmpeg.FFprobe):

    executable = STATIC_FFPROBE_BINARY

    def get_media_info(self, filename):
        if filename == 'small.mp4' and not WITH_FFMPEG:
            return MEDIA_INFOS
        return super(MockFFprobe, self).get_media_info(filename)


class MockEncodeStatistics(ffmpeg.EncodeStatistics):

    ffprobe_class = MockFFprobe


class RaiseEncodeStatistics(ffmpeg.EncodeStatistics):

    def end(self, returncode):
        raise ValueError('This is the error.')


class RaiseFFmpeg(MockFFmpeg):

    statistics_class = RaiseEncodeStatistics


class TestUtils(FilterByTagsMixin, unittest.TestCase):

    tags = ('multimedia', 'ffmpeg')

    def test_to_bit_rate(self):
        self.assertEqual(to_bit_rate('231.5kbit/s'), 231500)
        self.assertEqual(to_bit_rate('3302.3kbits/s'), 3302300)
        self.assertEqual(to_bit_rate('1935.9kbits/s'), 1935900)
        self.assertIsNone(to_bit_rate('N/A'))

    def test_to_frame_rate(self):
        self.assertEqual(to_frame_rate('10.5'), 10.5)
        self.assertEqual(to_frame_rate(25.0), 25.0)
        self.assertEqual(to_frame_rate('59000/1000'), 59.0)
        self.assertIsNone(to_frame_rate('10/0'))

    def test_to_size(self):
        self.assertEqual(to_size('231.5kB'), 237056)
        self.assertEqual(to_size('3302.3MB'), 3462712524)
        self.assertEqual(to_size('1935.9KB'), 1982361)


class TestMedia(FilterByTagsMixin, unittest.TestCase):

    tags = ('multimedia', 'ffmpeg')

    def test_pipe(self):
        self.assertFalse(Media(None).is_pipe)
        self.assertFalse(Media('test-file.mp4').is_pipe)
        for filename in '-', 'pipe:3':
            media = Media(filename)
            self.assertIsNone(media.directory)
            self.assertTrue(media.is_pipe)
            self.assertEqual(media.size, 0)


class TestEncodeStatistics(FilterByTagsMixin, unittest.TestCase):

    tags = ('multimedia', 'ffmpeg')

    inputs = [Media('small.mp4')]
    outputs = [Media('ff_output.mp4')]

    def get_statistics(self, start=False, returncode=None, options=None, **kwargs):
        if options is None:
            options = ['-acodec', 'copy', '-vcodec', 'copy']
        statistics = MockEncodeStatistics(self.inputs, self.outputs, options, **kwargs)
        start = start or returncode is not None
        if start:
            statistics.start('process')
        if returncode is not None:
            statistics.progress('')
            statistics.end(returncode)
        return statistics

    def test_get_subclip_duration_and_size(self):
        eq, subclip = self.assertTupleEqual, self.get_statistics()._get_subclip_duration_and_size
        duration = datetime.timedelta(hours=1, minutes=30, seconds=36.5)
        sub_dur_1 = datetime.timedelta(seconds=3610.2)
        sub_dur_2 = datetime.timedelta(hours=1, minutes=20, seconds=15.8)
        sub_dur_3 = datetime.timedelta(minutes=40, seconds=36.3)
        sub_dur_4 = datetime.timedelta(0)
        eq(subclip(duration, 512 * 1024, []), (duration, 512 * 1024))
        eq(subclip(duration, 512 * 1024, ['-t']), (duration, 512 * 1024))
        eq(subclip(duration, 512 * 1024, ['-t', '-t']), (duration, 512 * 1024))
        eq(subclip(duration, 512 * 1024, ['-t', '3610.2']), (sub_dur_1, 348162))
        eq(subclip(duration, 512 * 1024, ['-t', '01:20:15.8']), (sub_dur_2, 464428))
        eq(subclip(duration, 512 * 1024, ['-t', '01:20:15.8', '-ss', '00:50:00.2']), (sub_dur_3, 234953))
        eq(subclip(duration, 512 * 1024, ['-t', '01:20:15.8', '-ss', '01:30:36.5']), (sub_dur_4, 0))
        eq(subclip(duration, 512 * 1024, ['-ss', '01:30:53']), (sub_dur_4, 0))
        eq(subclip(duration, 512 * 1024, ['-t', '02:00:00.0']), (duration, 512 * 1024))

    def test_parse_chunk(self):
        statistics = self.get_statistics()
        eq, parse = self.assertDictEqual, statistics._parse_chunk
        self.assertIsNone(parse('Random stuff'))
        eq(parse('    frame= 2071 fps=  0 q=-1.0 size=   34623kB time=00:01:25.89 bitrate=3302.3kbits/s  '), {
            'frame': 2071, 'frame_rate': 0.0, 'qscale': -1.0, 'size': 34623 * 1024,
            'time': datetime.timedelta(minutes=1, seconds=25.89), 'bit_rate': 3302300
        })

    def test_should_report_initialization(self):
        statistics = self.get_statistics()
        self.assertTrue(statistics._should_report())
        self.assertEqual(statistics._prev_elapsed_time, datetime.timedelta(0))
        self.assertEqual(statistics._prev_ratio, 0)
        self.assertFalse(statistics._should_report())

    def test_should_report_elapsed_time_criteria(self):
        statistics = self.get_statistics()
        self.assertTrue(statistics._should_report())
        statistics.elapsed_time = datetime.timedelta(seconds=3)
        self.assertFalse(statistics._should_report())
        statistics.elapsed_time = datetime.timedelta(seconds=6)
        self.assertTrue(statistics._should_report())
        self.assertFalse(statistics._should_report())

    def test_should_report_ratio_criteria(self):
        statistics = self.get_statistics()
        self.assertTrue(statistics._should_report())
        statistics.ratio = 0.001
        self.assertFalse(statistics._should_report())
        statistics.ratio = 0.02
        self.assertFalse(statistics._should_report())
        statistics.elapsed_time = datetime.timedelta(seconds=2)
        self.assertTrue(statistics._should_report())
        self.assertFalse(statistics._should_report())

    def test_eta_time(self):
        statistics = self.get_statistics()
        statistics.elapsed_time = datetime.timedelta(seconds=60)
        self.assertIsNone(statistics.eta_time)
        statistics.ratio = 0.0
        self.assertIsNone(statistics.eta_time)
        statistics.ratio = 0.2
        self.assertEqual(statistics.eta_time, datetime.timedelta(seconds=240))
        statistics.ratio = 0.5
        self.assertEqual(statistics.eta_time, datetime.timedelta(seconds=60))
        statistics.ratio = 1.0
        self.assertEqual(statistics.eta_time, datetime.timedelta(0))

    def test_compute_ratio(self):
        statistics = self.get_statistics()
        statistics.input.duration = datetime.timedelta(seconds=0)
        statistics.output.duration = None
        self.assertIsNone(statistics._compute_ratio())
        statistics.input.duration = datetime.timedelta(seconds=0)
        statistics.output.duration = datetime.timedelta(0)
        self.assertIsNone(statistics._compute_ratio())
        statistics.input.duration = datetime.timedelta(seconds=1)
        self.assertEqual(statistics._compute_ratio(), 0.0)
        statistics.input.duration = datetime.timedelta(seconds=60)
        statistics.output.duration = datetime.timedelta(seconds=30)
        self.assertEqual(statistics._compute_ratio(), 0.5)

    def test_new_properties(self):
        statistics = self.get_statistics()
        self.assertEqual(statistics.state, statistics.states.NEW)
        self.assertIsInstance(statistics.input.duration, datetime.timedelta)
        self.assertIsNone(statistics.eta_time)
        self.assertEqual(statistics.input, statistics.inputs[0])
        self.assertEqual(statistics.output, statistics.outputs[0])
        self.assertIsNone(statistics.ratio)
        self.assertIsNotNone(statistics.input._size)

    def test_started_properties(self):
        statistics = self.get_statistics(start=True)
        self.assertEqual(statistics.state, statistics.states.STARTED)
        self.assertEqual(statistics.output.duration, datetime.timedelta(0))
        self.assertIsNone(statistics.eta_time)
        self.assertEqual(statistics.ratio, 0.0)

    def test_success_properties(self):
        self.outputs[0].filename = self.inputs[0].filename
        statistics = self.get_statistics(returncode=0)
        self.assertEqual(statistics.state, statistics.states.SUCCESS)
        self.assertEqual(statistics.output.duration, statistics.input.duration)
        self.assertEqual(statistics.eta_time, datetime.timedelta(0))
        self.assertEqual(statistics.ratio, 1.0)
        self.assertIsNone(statistics.output._size)


class TestFFmpeg(FilterByTagsMixin, unittest.TestCase):

    tags = ('multimedia', 'ffmpeg')

    def setUp(self):
        self.ffmpeg = MockFFmpeg()

    def test_clean_medias_argument(self):
        eq = self.assertListEqual
        clean = self.ffmpeg._clean_medias_argument
        eq(clean(None), [])
        eq(clean([]), [])
        eq(clean('a.mp4'), [Media('a.mp4')])
        eq(clean(['a.mp4', 'b.mp3']), [Media('a.mp4'), Media('b.mp3')])
        eq(clean(Media('a', '-f mp4')), [Media('a', ['-f', 'mp4'])])
        eq(clean([Media('a', ['-f', 'mp4']), Media('b.mp3')]), [Media('a', ['-f', 'mp4']), Media('b.mp3')])

    @unittest.skipIf(not WITH_FFMPEG, 'Static FFmpeg binary not available')
    def test_encode(self):
        results = list(self.ffmpeg.encode(Media('small.mp4'), Media('ff_output.mp4', '-c:a copy -c:v copy')))
        self.assertTrue(try_remove('ff_output.mp4'))
        self.assertEqual(results[-1].state, EncodeState.SUCCESS)

        results = list(self.ffmpeg.encode(Media('small.mp4'), Media('ff_output.mp4', 'crazy_option')))
        self.assertFalse(try_remove('ff_output.mp4'))
        self.assertEqual(results[-1].state, EncodeState.FAILURE)

        results = list(self.ffmpeg.encode([Media('missing.mp4')], Media('ff_output.mp4', '-c:a copy -c:v copy')))
        self.assertFalse(try_remove('ff_output.mp4'))
        self.assertEqual(results[-1].state, EncodeState.FAILURE)

    def test_get_arguments(self):
        eq = self.assertListEqual
        get = self.ffmpeg._get_arguments
        self.ffmpeg.executable = 'ffmpeg'

        # Using options (the legacy API, also simplify simple calls)
        options_string = '-strict experimental -vf "yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2"'

        args, inputs, outputs, options = get('input.mp4', 'output.mkv', options_string)
        eq(inputs, [Media('input.mp4')])
        eq(outputs, [Media('output.mkv')])
        eq(options, ['-strict', 'experimental', '-vf', 'yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2'])
        eq(args, ['ffmpeg', '-y', '-i', 'input.mp4'] + options + ['output.mkv'])

        args, _, outputs, options = get('input.mp4', None, options_string)
        eq(outputs, [])
        eq(args, ['ffmpeg', '-y', '-i', 'input.mp4'] + options)

        # Using instances of Media (the newest API, greater flexibility)
        args, inputs, outputs, options = get(Media('in', '-f mp4'), Media('out.mkv', '-acodec copy -vcodec copy'))
        eq(inputs, [Media('in', ['-f', 'mp4'])])
        eq(outputs, [Media('out.mkv', ['-acodec', 'copy', '-vcodec', 'copy'])])
        eq(options, [])
        eq(args, ['ffmpeg', '-y', '-f', 'mp4', '-i', 'in', '-acodec', 'copy', '-vcodec', 'copy', 'out.mkv'])

    @unittest.skipIf(not WITH_FFMPEG, 'Static FFmpeg binary not available')
    def test_get_process(self):
        options = ['-strict', 'experimental', '-vf', 'yadif=0.-1:0, scale=trunc(iw/2)*2:trunc(ih/2)*2']
        process = self.ffmpeg._get_process([STATIC_FFMPEG_BINARY, '-y', '-i', 'input.mp4'] + options + ['output.mkv'])
        self.assertListEqual(process.args, [STATIC_FFMPEG_BINARY, '-y', '-i', 'input.mp4'] + options + ['output.mkv'])
        process.terminate()

    @unittest.skipIf(not WITH_FFMPEG, 'Static FFmpeg binary not available')
    def test_kill_process_handle_missing(self):
        encoder = RaiseFFmpeg()
        with self.assertRaises(ValueError):
            list(encoder.encode('small.mp4', 'ff_output.mp4', '-c:a copy -c:v copy'))
        self.assertTrue(try_remove('ff_output.mp4'))


class TestFFprobe(FilterByTagsMixin, unittest.TestCase):

    tags = ('multimedia', 'ffmpeg')

    def setUp(self):
        self.ffprobe = MockFFprobe()

    def test_get_audio_streams(self):
        self.ffprobe.stream_classes['audio'] = None
        streams = self.ffprobe.get_audio_streams('small.mp4')
        self.assertIsInstance(streams[0], dict)
        self.assertEqual(streams[0]['avg_frame_rate'], '0/0')
        self.assertEqual(streams[0]['channels'], 1)
        self.assertEqual(streams[0]['codec_time_base'], '1/48000')

        self.ffprobe.stream_classes['audio'] = AudioStream
        streams = self.ffprobe.get_audio_streams('small.mp4')
        self.assertIsInstance(streams[0], AudioStream)
        self.assertIsNone(streams[0].avg_frame_rate)
        self.assertEqual(streams[0].channels, 1)
        self.assertEqual(streams[0].codec.time_base, 1 / 48000)

    def test_get_media_duration(self):
        # Bad file format
        with open('/tmp/test.txt', 'w', encoding='utf-8') as f:
            f.write('Hey, I am not a MPD nor a média')
        self.assertIsNone(self.ffprobe.get_media_duration('/tmp/test.txt'))
        os.remove('/tmp/test.txt')

        # Some random bad things
        self.assertIsNone(self.ffprobe.get_media_duration({}))

        # A MPEG-DASH MPD
        with open('/tmp/test.mpd', 'w', encoding='utf-8') as f:
            f.write(MPD_TEST)
        self.assertEqual(self.ffprobe.get_media_duration('/tmp/test.mpd').strftime('%H:%M:%S.%f'), '00:06:07.830000')
        self.assertEqual(self.ffprobe.get_media_duration('/tmp/test.mpd', as_delta=True),
                         datetime.timedelta(0, 367, 830000))
        os.remove('/tmp/test.mpd')

        # A MP4
        self.assertEqual(self.ffprobe.get_media_duration('small.mp4').strftime('%H:%M:%S'), '00:00:05')
        self.assertEqual(
            self.ffprobe.get_media_duration(self.ffprobe.get_media_info('small.mp4')).strftime('%H:%M:%S'), '00:00:05'
        )
        self.assertEqual(
            self.ffprobe.get_media_duration(self.ffprobe.get_media_info('small.mp4'), as_delta=True).seconds, 5
        )

    def test_get_media_format(self):
        self.ffprobe.format_class = None
        media_format = self.ffprobe.get_media_format('small.mp4', fail=True)
        self.assertIsInstance(media_format, dict)
        self.assertEqual(media_format['bit_rate'], '551193')
        self.assertEqual(media_format['format_long_name'], 'QuickTime / MOV')
        self.assertEqual(media_format['probe_score'], 100)

        self.ffprobe.format_class = Format
        media_format = self.ffprobe.get_media_format('small.mp4', fail=True)
        self.assertIsInstance(media_format, Format)
        self.assertEqual(media_format.bit_rate, 551193)
        self.assertEqual(media_format.format_long_name, 'QuickTime / MOV')
        self.assertEqual(media_format.probe_score, 100)

    def test_get_video_streams(self):
        self.ffprobe.stream_classes['video'] = None
        streams = self.ffprobe.get_video_streams('small.mp4')
        self.assertIsInstance(streams[0], dict)
        self.assertEqual(streams[0]['avg_frame_rate'], '30/1')

        self.ffprobe.stream_classes['video'] = VideoStream
        streams = self.ffprobe.get_video_streams('small.mp4')
        self.assertIsInstance(streams[0], VideoStream)
        self.assertEqual(streams[0].avg_frame_rate, 30.0)

    def test_get_video_frame_rate(self):
        self.assertIsNone(self.ffprobe.get_video_frame_rate(3.14159265358979323846))
        self.assertIsNone(self.ffprobe.get_video_frame_rate({}))
        self.assertEqual(self.ffprobe.get_video_frame_rate(self.ffprobe.get_media_info('small.mp4')), 30.0)
        self.assertEqual(self.ffprobe.get_video_frame_rate('small.mp4'), 30.0)
        self.assertEqual(self.ffprobe.get_video_frame_rate({'streams': [
            {'codec_type': 'audio'},
            {'codec_type': 'video', 'avg_frame_rate': '59000/1000'}
        ]}), 59.0)

    def test_get_video_resolution(self):
        self.assertIsNone(self.ffprobe.get_video_resolution(3.14159265358979323846))
        self.assertIsNone(self.ffprobe.get_video_resolution({}))
        self.assertListEqual(self.ffprobe.get_video_resolution(self.ffprobe.get_media_info('small.mp4')), [560, 320])
        self.assertListEqual(self.ffprobe.get_video_resolution('small.mp4'), [560, 320])
        self.assertIsNone(self.ffprobe.get_video_resolution('small.mp4', index=1))
        self.assertEqual(self.ffprobe.get_video_resolution('small.mp4')[HEIGHT], 320)
        self.assertListEqual(self.ffprobe.get_video_resolution({'streams': [
            {'codec_type': 'audio'},
            {'codec_type': 'video', 'width': '1920', 'height': '1080'}
        ]}), [1920, 1080])
