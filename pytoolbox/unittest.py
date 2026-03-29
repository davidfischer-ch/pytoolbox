"""
Test mixins and assertion helpers for :mod:`unittest`-based test suites.
"""

from __future__ import annotations

import functools
import inspect
import io
import itertools
import os
import pprint
import shutil
import time
import unittest
from collections.abc import Callable, Generator, Iterator
from pathlib import Path
from typing import Any

from . import module
from .multimedia import ffmpeg
from .string import snake_to_camel
from .types import Missing

_all = module.All(globals())


def skip_if_missing(binary: str) -> Callable:
    """Ensure the binary is available or skip the test."""

    def _skip_if_missing(func: Callable) -> Any:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not shutil.which(binary):
                raise unittest.SkipTest(f'Missing binary {binary}')
            return func(*args, **kwargs)

        return wrapper

    return _skip_if_missing


def with_tags(
    tags: str | set[str] | None = None,
    required: str | set[str] | None = None,
) -> Callable:
    """Decorate a test method with filterable tags."""

    def _with_tags(f: Callable) -> Callable:
        f.tags = set([tags] if isinstance(tags, str) else tags or [])
        f.required_tags = set([required] if isinstance(required, str) else required or [])
        return f

    return _with_tags


class InMixin:
    """Mixin providing ``assertIn`` / ``assertNotIn`` with sorted output."""

    @staticmethod
    def assert_in_hook(obj: Any) -> Any:
        """Return *obj* sorted if it is not a string or bytes sequence."""
        return obj if isinstance(obj, (str, bytes)) else sorted(obj)

    def assertIn(  # pylint:disable=invalid-name  # noqa: N802
        self,
        obj_a: Any,
        obj_b: Any,
        msg: str | None = None,
    ) -> None:
        """Assert that *obj_a* is contained in *obj_b*."""
        assert obj_a in obj_b, f'{obj_a} not in {self.assert_in_hook(obj_b)}: {msg or ""}'

    def assertNotIn(  # pylint:disable=invalid-name  # noqa: N802
        self,
        obj_a: Any,
        obj_b: Any,
        msg: str | None = None,
    ) -> None:
        """Assert that *obj_a* is not contained in *obj_b*."""
        assert obj_a not in obj_b, f'{obj_a} in {self.assert_in_hook(obj_b)}: {msg or ""}'


class InspectMixin:
    """Mixin providing introspection of test methods."""

    @property
    def current_test(self) -> Callable:
        """Return the bound method for the currently running test."""
        return getattr(self, self.id().split('.')[-1])

    @classmethod
    def get_test_methods(cls) -> Iterator[tuple[str, Callable]]:
        """Return an iterator of ``(name, method)`` for all test methods."""
        return (
            (n, m)
            for n, m in inspect.getmembers(cls)
            if n.startswith('test_') and hasattr(m, '__call__')
        )


class AwareTearDownMixin:
    """Mixin calling :meth:`awareTearDown` with the test result after each run."""

    def awareTearDown(self, result: unittest.TestResult) -> None:  # noqa: N802
        """Handle post-test cleanup with access to the test *result*."""
        pass  # de bleu, c'est fantastique !  # pylint:disable=unnecessary-pass

    def run(self, result: unittest.TestResult | None = None) -> unittest.TestResult:
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
    def should_run(
        tags: set[str],
        required_tags: set[str],
        extra_tags: set[str],
        only_tags: set[str],
        skip_tags: set[str],
    ) -> bool:
        """Return ``True`` if a test with the given tags should be executed."""
        all_tags = tags | required_tags
        if all_tags & skip_tags:
            return False
        if only_tags and not all_tags & only_tags:
            return False
        if required_tags and not required_tags & (only_tags | extra_tags):
            return False
        return True

    @classmethod
    def setUpClass(cls) -> None:  # pylint:disable=invalid-name
        if cls.fast_class_skip_enabled:
            cls.fast_class_skip()
        super().setUpClass()

    @classmethod
    def fast_class_skip(cls) -> None:
        """Skip the entire test class if no test method should run."""
        methods = cls.get_test_methods()
        should_run = functools.partial(
            cls.should_run,
            extra_tags=cls.get_extra_tags(),
            only_tags=cls.get_only_tags(),
            skip_tags=cls.get_skip_tags(),
        )
        if not any(should_run(cls.get_tags(m), cls.get_required_tags(m)) for n, m in methods):
            raise unittest.SkipTest('Test skipped by FilterByTagsMixin.fast_class_skip')

    @classmethod
    def get_extra_tags(cls) -> set[str]:
        """Return extra tags from the environment variable."""
        return set(t for t in os.environ.get(cls.extra_tags_variable, '').split(',') if t)

    @classmethod
    def get_only_tags(cls) -> set[str]:
        """Return only-run tags from the environment variable."""
        return set(t for t in os.environ.get(cls.only_tags_variable, '').split(',') if t)

    @classmethod
    def get_skip_tags(cls) -> set[str]:
        """Return skip tags from the environment variable."""
        return set(t for t in os.environ.get(cls.skip_tags_variable, '').split(',') if t)

    @classmethod
    def get_tags(cls, current_test: Callable) -> set[str]:
        """Return the combined tags for *current_test* including class-level tags."""
        my_id = (cls.__name__, current_test.__name__)
        return set(
            itertools.chain(
                cls.tags,
                getattr(current_test, 'tags', ()),
                (my_id[0], '.'.join(my_id)),
            ),
        )

    @classmethod
    def get_required_tags(cls, current_test: Callable) -> set[str]:
        """Return the combined required tags for *current_test*."""
        return set(itertools.chain(cls.required_tags, getattr(current_test, 'required_tags', ())))

    def setUp(self) -> None:  # pylint:disable=invalid-name
        if not self.should_run(
            self.get_tags(self.current_test),
            self.get_required_tags(self.current_test),
            self.get_extra_tags(),
            self.get_only_tags(),
            self.get_skip_tags(),
        ):
            raise unittest.SkipTest('Test skipped by FilterByTagsMixin.setUp')
        super().setUp()


class FFmpegMixin:
    """Mixin providing FFmpeg/FFprobe assertions for media tests."""

    ffmpeg_class = ffmpeg.FFmpeg

    @classmethod
    def setUpClass(cls) -> None:  # pylint:disable=invalid-name
        for name, stream_class in cls.ffmpeg_class.ffprobe_class.stream_classes.items():
            assert stream_class is not None, name
            assert stream_class.codec_class is not None, name
        super().setUpClass()

    def setUp(self) -> None:  # pylint:disable=invalid-name
        super().setUp()
        self.ffmpeg = self.ffmpeg_class()
        self.ffprobe = self.ffmpeg.ffprobe_class()

    # Codecs Asserts

    def assertMediaCodecEqual(  # noqa: N802
        self,
        path: str | Path,
        stream_type: str,
        index: int,
        **codec_attrs: Any,
    ) -> None:
        """Assert that the codec attributes of a stream match expected values."""
        codec = getattr(self.ffprobe, f'get_{stream_type}_streams')(path)[index].codec
        for attr, value in codec_attrs.items():
            self.assertEqual(getattr(codec, attr), value, msg=f'Codec attribute {attr}')

    def assertAudioCodecEqual(  # noqa: N802
        self,
        path: str | Path,
        index: int,
        **codec_attrs: Any,
    ) -> None:
        """Assert that the audio codec at *index* matches expected attributes."""
        self.assertMediaCodecEqual(path, 'audio', index, **codec_attrs)

    def assertSubtitleCodecEqual(  # noqa: N802
        self,
        path: str | Path,
        index: int,
        **codec_attrs: Any,
    ) -> None:
        """Assert that the subtitle codec at *index* matches expected attributes."""
        self.assertMediaCodecEqual(path, 'subtitle', index, **codec_attrs)

    def assertVideoCodecEqual(  # pylint:disable=invalid-name  # noqa: N802
        self,
        path: str | Path,
        index: int,
        **codec_attrs: Any,
    ) -> None:
        """Assert that the video codec at *index* matches expected attributes."""
        self.assertMediaCodecEqual(path, 'video', index, **codec_attrs)

    # Streams Asserts

    def assertAudioStreamEqual(  # pylint:disable=invalid-name  # noqa: N802
        self,
        first_path: str | Path,
        second_path: str | Path,
        first_index: int,
        second_index: int,
        *,
        same_codec: bool = True,
    ) -> None:
        """Assert that two audio streams have equal codec and bit rate."""
        first = self.ffprobe.get_audio_streams(first_path)[first_index]
        second = self.ffprobe.get_audio_streams(second_path)[second_index]
        if same_codec:
            self.assertEqual(first.codec, second.codec, msg='Codec mistmatch.')
        self.assertEqual(first.bit_rate, second.bit_rate, msg='Bit rate mistmatch.')

    def assertMediaFormatEqual(  # pylint:disable=invalid-name  # noqa: N802
        self,
        first_path: str | Path,
        second_path: str | Path,
        *,
        same_bit_rate: bool = True,
        same_duration: bool = True,
        same_size: bool = True,
        same_start_time: bool = True,
    ) -> None:
        """Assert that two media files have equal format metadata."""
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

    def assertVideoStreamEqual(  # noqa: N802
        self,
        first_path: str | Path,
        second_path: str | Path,
        first_index: int,
        second_index: int,
        *,
        same_codec: bool = True,
    ) -> None:
        """Assert that two video streams have equal codec, frame rate, and dimensions."""
        first = self.ffprobe.get_video_streams(first_path)[first_index]
        second = self.ffprobe.get_video_streams(second_path)[second_index]
        if same_codec:
            self.assertEqual(first.codec, second.codec, msg='Codec mismatch.')
        self.assertRelativeEqual(
            first.avg_frame_rate,
            second.avg_frame_rate,
            msg='Average frame rate mismatch.',
        )
        if first.nb_frames:
            self.assertRelativeEqual(
                first.nb_frames,
                second.nb_frames,
                msg='Number of frames mistmatch.',
            )
        self.assertEqual(first.height, second.height, msg='Height mismatch.')
        self.assertEqual(first.width, second.width, msg='Width mismatch.')

    # Encoding Asserts

    def assertEncodeFailure(  # pylint:disable=invalid-name  # noqa: N802
        self,
        generator: Generator,
    ) -> list:
        """Assert that the encode *generator* ends in a failure state."""
        return self.assertEncodeState(generator, state=ffmpeg.EncodeState.FAILURE)

    def assertEncodeSuccess(self, generator: Generator) -> list:  # noqa: N802
        """Assert that the encode *generator* ends in a success state."""
        return self.assertEncodeState(generator, state=ffmpeg.EncodeState.SUCCESS)

    def assertEncodeState(  # noqa: N802
        self,
        generator: Generator,
        state: ffmpeg.EncodeState,
    ) -> list:
        """Assert that the encode *generator* ends in the expected *state*."""
        results = list(generator)
        result = io.StringIO()
        statistics = results[-1]
        pprint.pprint(
            {a: getattr(statistics, a) for a in dir(statistics) if a[0] != '_'},
            stream=result,
        )
        self.assertEqual(statistics.state, state, result.getvalue())
        return results


class MissingMixin:
    """Mixin providing assertions for the :data:`~pytoolbox.types.Missing` sentinel."""

    def assertIsMissing(  # pylint:disable=invalid-name  # noqa: N802
        self,
        value: Any,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Assert that *value* is the :data:`~pytoolbox.types.Missing` sentinel."""
        return self.assertIs(value, Missing, *args, **kwargs)

    def assertIsNotMissing(  # pylint:disable=invalid-name  # noqa: N802
        self,
        value: Any,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Assert that *value* is not the :data:`~pytoolbox.types.Missing` sentinel."""
        return self.assertIsNot(value, Missing, *args, **kwargs)


class SnakeCaseMixin:  # pylint:disable=too-few-public-methods
    """Mixin allowing snake_case access to camelCase assertion methods."""

    def __getattr__(self, name: str) -> Any:
        if name.lower() == name:
            attribute = snake_to_camel(name if name.startswith('assert_') else f'assert_{name}')
            return getattr(self, attribute)
        raise AttributeError


class TimingMixin:
    """Mixin that logs each test's execution time."""

    timing_logger = None

    def setUp(self) -> None:  # pylint:disable=invalid-name
        self.start_time = time.time()
        super().setUp()

    def tearDown(self) -> None:  # pylint:disable=invalid-name
        super().tearDown()
        if self.timing_logger:
            self.timing_logger.info(f'{self.id()}: {time.time() - self.start_time:.3f}')


class Asserts(InMixin, MissingMixin, SnakeCaseMixin, unittest.TestCase):
    """Standalone assertion helper combining all assertion mixins."""

    def runTest(self, *args: Any, **kwargs: Any) -> None:  # noqa: N802
        """No-op required by :class:`unittest.TestCase` for standalone use."""


asserts = Asserts()

__all__ = _all.diff(globals())
