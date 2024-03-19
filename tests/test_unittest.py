from __future__ import annotations

import unittest

from pytoolbox.types import Missing
from pytoolbox.unittest import asserts, with_tags, FilterByTagsMixin, MissingMixin, SnakeCaseMixin


def test_asserts() -> None:
    asserts.true(True)
    asserts.false(False)
    with asserts.raises(AssertionError):
        asserts.false(True)
    asserts.is_none(None)


def test_should_run() -> None:
    assert FilterByTagsMixin.should_run(set(), set(), set(), set(), set()) is True
    assert FilterByTagsMixin.should_run(set(), set(), set(), set(), {'b'}) is True
    assert FilterByTagsMixin.should_run(set(), set(), set(), {'a'}, set()) is False
    assert FilterByTagsMixin.should_run(set(), set(), set(), {'a'}, {'b'}) is False
    assert FilterByTagsMixin.should_run(set(), {'a'}, set(), set(), set()) is False
    assert FilterByTagsMixin.should_run(set(), {'a'}, set(), {'a'}, set()) is True
    assert FilterByTagsMixin.should_run({'a', 'b'}, set(), set(), set(), set()) is True
    assert FilterByTagsMixin.should_run({'a', 'b'}, set(), set(), set(), {'c', 'd'}) is True
    assert FilterByTagsMixin.should_run({'a', 'b'}, set(), set(), set(), {'c', 'b'}) is False
    assert FilterByTagsMixin.should_run({'a', 'b'}, set(), set(), {'c', 'a'}, set()) is True
    assert FilterByTagsMixin.should_run({'a', 'b'}, {'c', 'd'}, set(), {'c', 'a'}, set()) is True
    assert FilterByTagsMixin.should_run({'a', 'b'}, set(), set(), {'a'}, {'c', 'd'}) is True
    assert FilterByTagsMixin.should_run({'a', 'b'}, set(), set(), {'b'}, {'b'}) is False


def test_should_run_with_extra() -> None:
    assert FilterByTagsMixin.should_run(set(), set(), {'a'}, set(), set()) is True
    assert FilterByTagsMixin.should_run(set(), set(), {'a'}, set(), {'b'}) is True
    assert FilterByTagsMixin.should_run(set(), set(), {'a'}, {'a'}, set()) is False
    assert FilterByTagsMixin.should_run(set(), set(), {'a'}, {'a'}, {'b'}) is False
    assert FilterByTagsMixin.should_run(set(), {'a'}, {'a'}, set(), set()) is True
    assert FilterByTagsMixin.should_run(set(), {'a'}, {'a'}, {'a'}, set()) is True
    assert FilterByTagsMixin.should_run({'a', 'b'}, set(), {'a'}, set(), set()) is True
    assert FilterByTagsMixin.should_run({'a', 'b'}, set(), {'a'}, set(), {'c', 'd'}) is True
    assert FilterByTagsMixin.should_run({'a', 'b'}, set(), {'a'}, set(), {'c', 'b'}) is False
    assert FilterByTagsMixin.should_run({'a', 'b'}, set(), {'a'}, {'c', 'a'}, set()) is True
    assert FilterByTagsMixin.should_run({'a', 'b'}, {'c', 'd'}, {'a'}, {'c', 'a'}, set()) is True
    assert FilterByTagsMixin.should_run({'a', 'b'}, set(), {'a'}, {'a'}, {'c', 'd'}) is True
    assert FilterByTagsMixin.should_run({'a', 'b'}, set(), {'a'}, {'b'}, {'b'}) is False


class TestFilterByTagsMixin(FilterByTagsMixin, unittest.TestCase):

    def test_fast_class_skip(self) -> None:

        class TestCaseWithTags(FilterByTagsMixin):
            tags = {'c'}
            fast_class_skip_enabled = True

            @classmethod
            def get_only_tags(cls):
                return cls.only_tags

            @classmethod
            def get_extra_tags(cls):
                return cls.extra_tags

            @classmethod
            def get_skip_tags(cls):
                return cls.skip_tags

            @with_tags('m')
            def test_1(self):
                pass

            @with_tags(required='r')
            def test_2(self):
                pass

        def test(counter, skip, extra_tags=None, only_tags=None, skip_tags=None) -> None:
            skipped = False
            try:
                TestCaseWithTags.extra_tags = extra_tags or set()
                TestCaseWithTags.only_tags = only_tags or set()
                TestCaseWithTags.skip_tags = skip_tags or set()
                TestCaseWithTags.fast_class_skip()
            except unittest.SkipTest:
                skipped = True
            msg = []
            for name, method in TestCaseWithTags.get_test_methods():
                args = (
                    TestCaseWithTags.get_tags(method),
                    TestCaseWithTags.get_required_tags(method),
                    TestCaseWithTags.get_extra_tags(),
                    TestCaseWithTags.get_only_tags(),
                    TestCaseWithTags.get_skip_tags()
                )
                msg.append([counter, name, TestCaseWithTags.should_run(*args), args])
            assert skipped == skip, msg

        test(1, False)
        test(2, True, skip_tags={'c'})
        test(3, True, skip_tags={'TestCaseWithTags.test_1'})
        test(4, False, skip_tags={'TestCaseWithTags.test_2'})
        test(5, True, extra_tags={'r'}, skip_tags={'c'})
        test(6, False, extra_tags={'r'}, skip_tags={'m'})
        test(7, True, extra_tags={'r'}, skip_tags={'TestCaseWithTags'})
        test(8, False, extra_tags={'r'}, skip_tags={'TestCaseWithTags.a'})
        test(9, False, extra_tags={'r'}, skip_tags={'TestCaseWithTags.test_1'})
        test(10, True, extra_tags={'r'}, skip_tags={
            'TestCaseWithTags.test_1', 'TestCaseWithTags.test_2'
        })
        test(11, False, extra_tags={'r'}, skip_tags={'AnotherTestCase'})

    @with_tags(required='should-not-run')
    def test_with_tags_decorator(self) -> None:
        raise RuntimeError('This test should never run.')


class TestMissingAndSnakeCaseMixins(MissingMixin, SnakeCaseMixin, unittest.TestCase):

    def test_core(self) -> None:
        self.equal(10, 10)
        with self.raises(AssertionError):
            self.equal(10, 2)
        self.dict_equal({}, {})
        with self.raises(AssertionError):
            self.dict_equal({}, {'a': 'b'})
        self.true(True)
        self.false(False)

    def test_missing(self) -> None:
        self.is_missing(Missing)
        self.is_not_missing(None)
