# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import functools, inspect, io, itertools, os, pprint, time, unittest

from . import module
from .encoding import binary_type, string_types
from .multimedia import ffmpeg
from .string import snake_to_camel
from .types import Missing

_all = module.All(globals())


def mock_cmd(stdout='', stderr='', returncode=0):
    import mock
    return mock.Mock(return_value={'stdout': stdout, 'stderr': stderr, 'returncode': returncode})


def runtests(test_file, cover_packages, packages, ignore=None, extra_options=None):
    """Run tests and report coverage with nose and coverage."""
    import nose
    from .encoding import configure_unicode
    configure_unicode()
    nose_options = filter(None, itertools.chain(
        [test_file, '--with-doctest', '--with-coverage', '--cover-erase', '--exe'],
        ['--cover-package={0}'.format(package) for package in cover_packages],
        ['--cover-html', '-vv', '-w', os.path.dirname(test_file)],
        packages, extra_options or []
    ))
    if ignore:
        nose_options += ['-I', ignore]
    os.chdir(os.path.abspath(os.path.dirname(test_file)))
    return nose.main(argv=nose_options)


def with_tags(tags=None, required=None):
    def _with_tags(f):
        f.tags = set([tags] if isinstance(tags, string_types) else tags or [])
        f.required_tags = set([required] if isinstance(required, string_types) else required or [])
        return f
    return _with_tags


class InMixin(object):

    def assert_in_hook(self, b):
        return b if isinstance(b, (string_types, binary_type)) else sorted(b)

    def assertIn(self, a, b, msg=None):
        assert a in b, '{0} not in {1}: {2}'.format(a, self.assert_in_hook(b), msg or '')

    def assertNotIn(self, a, b, msg=None):
        assert a not in b, '{0} in {1}: {2}'.format(a, self.assert_in_hook(b), msg or '')


class InspectMixin(object):

    @property
    def current_test(self):
        return getattr(self, self.id().split('.')[-1])

    @classmethod
    def get_test_methods(cls):
        return (
            (n, m) for n, m in inspect.getmembers(cls)
            if n.startswith('test_') and hasattr(m, '__call__')
        )


class AwareTearDownMixin(object):

    def awareTearDown(self, result):
        pass  # de bleu, c'est fantastique !

    def run(self, result=None):
        result = super(AwareTearDownMixin, self).run(result)
        self.awareTearDown(result)
        return result


class FilterByTagsMixin(InspectMixin):
    """
    Allow to filter unit-tests by tags, including by default, the `TestCaseName` and
    `TestCaseName.method_name`.
    """

    tags = required_tags = ()
    fast_class_skip_enabled = False
    extra_tags_variable = 'TEST_EXTRA_TAGS'
    only_tags_variable = 'TEST_ONLY_TAGS'
    skip_tags_variable = 'TEST_SKIP_TAGS'

    @staticmethod
    def should_run(tags, required_tags, extra_tags, only_tags, skip_tags):
        all_tags = tags | required_tags
        if all_tags & skip_tags:
            return False
        if only_tags and not all_tags & only_tags:
            return False
        if required_tags and not required_tags & (only_tags | extra_tags):
            return False
        return True

    @classmethod
    def setUpClass(cls):
        if cls.fast_class_skip_enabled:
            cls.fast_class_skip()
        super(FilterByTagsMixin, cls).setUpClass()

    @classmethod
    def fast_class_skip(cls):
        r = functools.partial(
            cls.should_run,
            extra_tags=cls.get_extra_tags(),
            only_tags=cls.get_only_tags(),
            skip_tags=cls.get_skip_tags()
        )
        if not any(r(cls.get_tags(m), cls.get_required_tags(m)) for n, m in cls.get_test_methods()):
            raise unittest.SkipTest('Test skipped by FilterByTagsMixin.fast_class_skip')

    @classmethod
    def get_extra_tags(cls):
        return set(t for t in os.environ.get(cls.extra_tags_variable, '').split(',') if t)

    @classmethod
    def get_only_tags(cls):
        return set(t for t in os.environ.get(cls.only_tags_variable, '').split(',') if t)

    @classmethod
    def get_skip_tags(cls):
        return set(t for t in os.environ.get(cls.skip_tags_variable, '').split(',') if t)

    @classmethod
    def get_tags(cls, current_test):
        my_id = (cls.__name__, current_test.__name__)
        return set(itertools.chain(
            cls.tags, getattr(current_test, 'tags', ()), (my_id[0], '.'.join(my_id))))

    @classmethod
    def get_required_tags(cls, current_test):
        return set(itertools.chain(cls.required_tags, getattr(current_test, 'required_tags', ())))

    def setUp(self):
        if not self.should_run(
            self.get_tags(self.current_test),
            self.get_required_tags(self.current_test),
            self.get_extra_tags(),
            self.get_only_tags(),
            self.get_skip_tags()
        ):
            raise unittest.SkipTest('Test skipped by FilterByTagsMixin.setUp')
        super(FilterByTagsMixin, self).setUp()


class FFmpegMixin(object):

    ffmpeg_class = ffmpeg.FFmpeg

    @classmethod
    def setUpClass(cls):
        for name, stream_class in cls.ffmpeg_class.ffprobe_class.stream_classes.iteritems():
            assert stream_class is not None, name
            assert stream_class.codec_class is not None, name
        super(FFmpegMixin, cls).setUpClass()

    def setUp(self):
        super(FFmpegMixin, self).setUp()
        self.ffmpeg = self.ffmpeg_class()
        self.ffprobe = self.ffmpeg.ffprobe_class()

    # Codecs Asserts

    def assertMediaCodecEqual(self, path, stream_type, index, **codec_attrs):
        codec = getattr(self.ffprobe, 'get_{0}_streams'.format(stream_type))(path)[index].codec
        for attr, value in codec_attrs.iteritems():
            self.assertEqual(getattr(codec, attr), value, msg='Codec attribute {0}'.format(attr))

    def assertAudioCodecEqual(self, path, index, **codec_attrs):
        self.assertMediaCodecEqual(path, 'audio', index, **codec_attrs)

    def assertSubtitleCodecEqual(self, path, index, **codec_attrs):
        self.assertMediaCodecEqual(path, 'subtitle', index, **codec_attrs)

    def assertVideoCodecEqual(self, path, index, **codec_attrs):
        self.assertMediaCodecEqual(path, 'video', index, **codec_attrs)

    # Streams Asserts

    def assertAudioStreamEqual(self, first_path, second_path, first_index, second_index,
                               same_codec=True):
        first = self.ffprobe.get_audio_streams(first_path)[first_index]
        second = self.ffprobe.get_audio_streams(second_path)[second_index]
        if same_codec:
            self.assertEqual(first.codec, second.codec, msg='Codec mistmatch.')
        self.assertEqual(first.bit_rate, second.bit_rate, msg='Bit rate mistmatch.')

    def assertMediaFormatEqual(self, first_path, second_path, same_bit_rate=True,
                               same_duration=True, same_size=True, same_start_time=True):
        formats = [self.ffprobe.get_media_info(p)['format'] for p in (first_path, second_path)]
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

    def assertVideoStreamEqual(self, first_path, second_path, first_index, second_index,
                               same_codec=True):
        first = self.ffprobe.get_video_streams(first_path)[first_index]
        second = self.ffprobe.get_video_streams(second_path)[second_index]
        if same_codec:
            self.assertEqual(first.codec, second.codec, msg='Codec mismatch.')
        self.assertRelativeEqual(
            first.avg_frame_rate, second.avg_frame_rate, msg='Average frame rate mismatch.')
        if first.nb_frames:
            self.assertRelativeEqual(
                first.nb_frames, second.nb_frames, msg='Number of frames mistmatch.')
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
        pprint.pprint(
            {a: getattr(statistics, a) for a in dir(statistics) if a[0] != '_'}, stream=result)
        self.assertEqual(statistics.state, state, result.getvalue())
        return results


class MissingMixin(object):

    def assertIsMissing(self, value, *args, **kwargs):
        return self.assertIs(value, Missing, *args, **kwargs)

    def assertIsNotMissing(self, value, *args, **kwargs):
        return self.assertIsNot(value, Missing, *args, **kwargs)


class SnakeCaseMixin(object):

    def __getattr__(self, name):
        if name.lower() == name:
            return getattr(self, snake_to_camel(
                name if name.startswith('assert_') else 'assert_{0}'.format(name)))
        raise AttributeError


class TimingMixin(object):

    timing_logger = None

    def setUp(self):
        self.start_time = time.time()
        super(TimingMixin, self).setUp()

    def tearDown(self):
        super(TimingMixin, self).tearDown()
        if self.timing_logger:
            self.timing_logger.info('{0}: {1:.3f}'.format(self.id(), time.time() - self.start_time))


class Asserts(InMixin, MissingMixin, SnakeCaseMixin, unittest.TestCase):

    def runTest(self, *args, **kwargs):
        pass


asserts = Asserts()

__all__ = _all.diff(globals())
