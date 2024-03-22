# pylint:disable=no-member
from __future__ import annotations

import functools
import inspect
import io
import itertools
import os
import pprint
import time
import unittest

from . import module
from .multimedia import ffmpeg
from .string import snake_to_camel
from .types import Missing

_all = module.All(globals())


def with_tags(tags=None, required=None):
    def _with_tags(f):
        f.tags = set([tags] if isinstance(tags, str) else tags or [])
        f.required_tags = set([required] if isinstance(required, str) else required or [])
        return f
    return _with_tags


class InMixin(object):

    @staticmethod
    def assert_in_hook(obj):
        return obj if isinstance(obj, (str, bytes)) else sorted(obj)

    def assertIn(self, obj_a, obj_b, msg=None):  # pylint:disable=invalid-name
        assert obj_a in obj_b, f"{obj_a} not in {self.assert_in_hook(obj_b)}: {msg or ''}"

    def assertNotIn(self, obj_a, obj_b, msg=None):  # pylint:disable=invalid-name
        assert obj_a not in obj_b, f"{obj_a} in {self.assert_in_hook(obj_b)}: {msg or ''}"


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

    def awareTearDown(self, result):  # pylint:disable=invalid-name
        pass  # de bleu, c'est fantastique !

    def run(self, result=None):
        result = super().run(result)
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
    def setUpClass(cls):  # pylint:disable=invalid-name
        if cls.fast_class_skip_enabled:
            cls.fast_class_skip()
        super().setUpClass()

    @classmethod
    def fast_class_skip(cls):
        methods = cls.get_test_methods()
        should_run = functools.partial(
            cls.should_run,
            extra_tags=cls.get_extra_tags(),
            only_tags=cls.get_only_tags(),
            skip_tags=cls.get_skip_tags()
        )
        if not any(should_run(cls.get_tags(m), cls.get_required_tags(m)) for n, m in methods):
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
            cls.tags,
            getattr(current_test, 'tags', ()),
            (my_id[0], '.'.join(my_id)))
        )

    @classmethod
    def get_required_tags(cls, current_test):
        return set(itertools.chain(cls.required_tags, getattr(current_test, 'required_tags', ())))

    def setUp(self):  # pylint:disable=invalid-name
        if not self.should_run(
            self.get_tags(self.current_test),
            self.get_required_tags(self.current_test),
            self.get_extra_tags(),
            self.get_only_tags(),
            self.get_skip_tags()
        ):
            raise unittest.SkipTest('Test skipped by FilterByTagsMixin.setUp')
        super().setUp()


class FFmpegMixin(object):

    ffmpeg_class = ffmpeg.FFmpeg

    @classmethod
    def setUpClass(cls):  # pylint:disable=invalid-name
        for name, stream_class in cls.ffmpeg_class.ffprobe_class.stream_classes.items():
            assert stream_class is not None, name
            assert stream_class.codec_class is not None, name
        super().setUpClass()

    def setUp(self):  # pylint:disable=invalid-name
        super().setUp()
        self.ffmpeg = self.ffmpeg_class()
        self.ffprobe = self.ffmpeg.ffprobe_class()

    # Codecs Asserts

    def assertMediaCodecEqual(
        self,
        path,
        stream_type,
        index,
        **codec_attrs
    ):  # pylint:disable=invalid-name
        codec = getattr(self.ffprobe, f'get_{stream_type}_streams')(path)[index].codec
        for attr, value in codec_attrs.items():
            self.assertEqual(getattr(codec, attr), value, msg=f'Codec attribute {attr}')

    def assertAudioCodecEqual(self, path, index, **codec_attrs):  # pylint:disable=invalid-name
        self.assertMediaCodecEqual(path, 'audio', index, **codec_attrs)

    def assertSubtitleCodecEqual(self, path, index, **codec_attrs):  # pylint:disable=invalid-name
        self.assertMediaCodecEqual(path, 'subtitle', index, **codec_attrs)

    def assertVideoCodecEqual(self, path, index, **codec_attrs):  # pylint:disable=invalid-name
        self.assertMediaCodecEqual(path, 'video', index, **codec_attrs)

    # Streams Asserts

    def assertAudioStreamEqual(  # pylint:disable=invalid-name
        self,
        first_path,
        second_path,
        first_index,
        second_index,
        *,
        same_codec=True
    ):
        first = self.ffprobe.get_audio_streams(first_path)[first_index]
        second = self.ffprobe.get_audio_streams(second_path)[second_index]
        if same_codec:
            self.assertEqual(first.codec, second.codec, msg='Codec mistmatch.')
        self.assertEqual(first.bit_rate, second.bit_rate, msg='Bit rate mistmatch.')

    def assertMediaFormatEqual(  # pylint:disable=invalid-name
        self,
        first_path,
        second_path,
        *,
        same_bit_rate=True,
        same_duration=True,
        same_size=True,
        same_start_time=True
    ):
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

    def assertVideoStreamEqual(  # pylint:disable=invalid-name
        self,
        first_path,
        second_path,
        first_index,
        second_index,
        *,
        same_codec=True
    ):
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

    def assertEncodeFailure(self, generator):  # pylint:disable=invalid-name
        return self.assertEncodeState(generator, state=ffmpeg.EncodeState.FAILURE)

    def assertEncodeSuccess(self, generator):  # pylint:disable=invalid-name
        return self.assertEncodeState(generator, state=ffmpeg.EncodeState.SUCCESS)

    def assertEncodeState(self, generator, state):  # pylint:disable=invalid-name
        results = list(generator)
        result = io.StringIO()
        statistics = results[-1]
        pprint.pprint(
            {a: getattr(statistics, a) for a in dir(statistics) if a[0] != '_'},
            stream=result)
        self.assertEqual(statistics.state, state, result.getvalue())
        return results


class MissingMixin(object):

    def assertIsMissing(self, value, *args, **kwargs):  # pylint:disable=invalid-name
        return self.assertIs(value, Missing, *args, **kwargs)

    def assertIsNotMissing(self, value, *args, **kwargs):  # pylint:disable=invalid-name
        return self.assertIsNot(value, Missing, *args, **kwargs)


class SnakeCaseMixin(object):  # pylint:disable=too-few-public-methods

    def __getattr__(self, name):
        if name.lower() == name:
            attribute = snake_to_camel(name if name.startswith('assert_') else f'assert_{name}')
            return getattr(self, attribute)
        raise AttributeError


class TimingMixin(object):

    timing_logger = None

    def setUp(self):  # pylint:disable=invalid-name
        self.start_time = time.time()
        super().setUp()

    def tearDown(self):  # pylint:disable=invalid-name
        super().tearDown()
        if self.timing_logger:
            self.timing_logger.info(f'{self.id()}: {time.time() - self.start_time:.3f}')


class Asserts(InMixin, MissingMixin, SnakeCaseMixin, unittest.TestCase):

    def runTest(self, *args, **kwargs):  # pylint:disable=invalid-name
        pass


asserts = Asserts()

__all__ = _all.diff(globals())
