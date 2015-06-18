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

import io, itertools, nose, os, pprint, sys, time, unittest
from os.path import abspath, dirname

from .multimedia import ffmpeg

if sys.version_info[0] > 2:
    from unittest.mock import Mock
else:
    from mock import Mock

__all__ = ('Mock', 'mock_cmd', 'runtests', 'AwareTearDownMixin', 'FilterByTagsMixin', 'FFmpegMixin', 'TimingMixin')


def mock_cmd(stdout='', stderr='', returncode=0):
    return Mock(return_value={'stdout': stdout, 'stderr': stderr, 'returncode': returncode})


def runtests(test_file, cover_packages, packages, ignore=None, extra_options=None):
    """Run tests and report coverage with nose and coverage."""
    from .encoding import configure_unicode
    configure_unicode()
    extra_options = extra_options or []
    cover_packages = ['--cover-package={0}'.format(package) for package in cover_packages]
    nose_options = filter(None, [test_file, '--with-doctest', '--with-coverage', '--cover-erase', '--exe'] +
                          cover_packages + ['--cover-html', '-vv', '-w', dirname(test_file)] + packages + extra_options)
    if ignore:
        nose_options += ['-I', ignore]
    os.chdir(abspath(dirname(test_file)))
    return nose.main(argv=nose_options)


class AwareTearDownMixin(object):

    def awareTearDown(self, result):
        pass  # de bleu, c'est fantastique !

    def run(self, result=None):
        result = super(AwareTearDownMixin, self).run(result)
        self.awareTearDown(result)
        return result


class FilterByTagsMixin(object):
    """
    Allow to filter unit-tests by tags, including by default, the `TestCaseName` and `TestCaseName.method_name`.
    """

    tags = ()
    only_tags_variable = 'TEST_ONLY_TAGS'
    skip_tags_variable = 'TEST_SKIP_TAGS'

    def get_tags(self):
        my_id = self.id().split('.')
        return itertools.chain(self.tags, (my_id[-2], '.'.join(my_id[-2:])))

    def get_only_tags(self):
        return (t for t in os.environ.get(self.only_tags_variable, '').split(',') if t)

    def get_skip_tags(self):
        return (t for t in os.environ.get(self.skip_tags_variable, '').split(',') if t)

    def should_run(self, tags, only_tags, skip_tags):
        return not tags & skip_tags and (bool(tags & only_tags) if tags and only_tags else True)

    def setUp(self):
        super(FilterByTagsMixin, self).setUp()
        if not self.should_run(set(self.get_tags()), set(self.get_only_tags()), set(self.get_skip_tags())):
            raise unittest.SkipTest('Test skipped by FilterByTagsMixin')


class FFmpegMixin(object):

    ffmpeg_class = ffmpeg.FFmpeg

    @classmethod
    def setUpClass(cls):
        for name, stream_class in cls.ffmpeg_class.ffprobe_class.stream_classes.items():
            assert stream_class is not None, name
            assert stream_class.codec_class is not None, name
        super(FFmpegMixin, cls).setUpClass()

    def setUp(self):
        super(FFmpegMixin, self).setUp()
        self.ffmpeg = self.ffmpeg_class()
        self.ffprobe = self.ffmpeg.ffprobe_class()

    # Codecs Asserts

    def assertMediaCodecEqual(self, filename, stream_type, index, **codec_attrs):
        codec = getattr(self.ffprobe, 'get_{0}_streams'.format(stream_type))(filename)[index].codec
        for attr, value in codec_attrs.items():
            self.assertEqual(getattr(codec, attr), value, msg='Codec attribute {0}'.format(attr))

    def assertAudioCodecEqual(self, filename, index, **codec_attrs):
        self.assertMediaCodecEqual(filename, 'audio', index, **codec_attrs)

    def assertSubtitleCodecEqual(self, filename, index, **codec_attrs):
        self.assertMediaCodecEqual(filename, 'subtitle', index, **codec_attrs)

    def assertVideoCodecEqual(self, filename, index, **codec_attrs):
        self.assertMediaCodecEqual(filename, 'video', index, **codec_attrs)

    # Streams Asserts

    def assertAudioStreamEqual(self, first_filename, second_filename, first_index, second_index, same_codec=True):
        first = self.ffprobe.get_audio_streams(first_filename)[first_index]
        second = self.ffprobe.get_audio_streams(second_filename)[second_index]
        if same_codec:
            self.assertEqual(first.codec, second.codec, msg='Codec mistmatch.')
        self.assertEqual(first.bit_rate, second.bit_rate, msg='Bit rate mistmatch.')

    def assertMediaFormatEqual(self, first_filename, second_filename, same_bit_rate=True, same_duration=True,
                               same_size=True, same_start_time=True):
        formats = [self.ffprobe.get_media_info(f)['format'] for f in (first_filename, second_filename)]
        bit_rates, durations, sizes, start_times = [], [], [], []
        for the_format in formats:
            the_format.pop('filename')
            the_format.pop('tags', None)
            durations.append(float(the_format.pop('duration')))
            bit_rates.append(float(the_format.pop('bit_rate', 0)))
            sizes.append(int(the_format.pop('size')))
            start_times.append(float(the_format.pop('start_time')))
        if same_bit_rate:
            self.assertRelativeEqual(*bit_rates, msg='Bit rate mistmatch.')
        if same_duration:
            self.assertRelativeEqual(*durations, msg='Duration mistmatch.')
        if same_size:
            self.assertRelativeEqual(*sizes, msg='Size mistmatch.')
        if same_start_time:
            self.assertRelativeEqual(*start_times, msg='Start time mistmatch.')
        self.assertDictEqual(*formats)

    def assertVideoStreamEqual(self, first_filename, second_filename, first_index, second_index, same_codec=True):
        first = self.ffprobe.get_video_streams(first_filename)[first_index]
        second = self.ffprobe.get_video_streams(second_filename)[second_index]
        if same_codec:
            self.assertEqual(first.codec, second.codec, msg='Codec mismatch.')
        self.assertRelativeEqual(first.avg_frame_rate, second.avg_frame_rate, msg='Average frame rate mismatch.')
        if first.nb_frames:
            self.assertRelativeEqual(first.nb_frames, second.nb_frames, msg='Number of frames mistmatch.')
        self.assertEqual(first.height, second.height, msg='Height mismatch.')
        self.assertEqual(first.width, second.width, msg='Width mismatch.')

    # Encoding Asserts

    def assertEncodeFailure(self, generator):
        return self.assertEncodeState(generator, state=ffmpeg.EncodeState.FAILURE)

    def assertEncodeSuccess(self, generator):
        return self.assertEncodeState(generator, state=ffmpeg.EncodeState.SUCCESS)

    def assertEncodeState(self, generator, state):
        results = list(generator)
        result = io.StringIO()
        statistics = results[-1]
        pprint.pprint({a: getattr(statistics, a) for a in dir(statistics) if a[0] != '_'}, stream=result)
        self.assertEqual(statistics.state, state, result.getvalue())
        return results


class TimingMixin(object):

    timing_logger = None

    def setUp(self):
        self.start_time = time.time()
        super(TimingMixin, self).setUp()

    def tearDown(self):
        super(TimingMixin, self).tearDown()
        if self.timing_logger:
            self.timing_logger.info('{0}: {1:.3f}'.format(self.id(), time.time() - self.start_time))
