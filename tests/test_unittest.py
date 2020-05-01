import unittest

from pytoolbox.unittest import asserts, with_tags, FilterByTagsMixin
from pytoolbox.types import Missing

from . import base


class TestFilterByTagsMixin(base.TestCase):

    tags = ('unittest', )

    def test_should_run(self):
        self.true(FilterByTagsMixin.should_run(set(), set(), set(), set(), set()))
        self.true(FilterByTagsMixin.should_run(set(), set(), set(), set(), {'b'}))
        self.false(FilterByTagsMixin.should_run(set(), set(), set(), {'a'}, set()))
        self.false(FilterByTagsMixin.should_run(set(), set(), set(), {'a'}, {'b'}))
        self.false(FilterByTagsMixin.should_run(set(), {'a'}, set(), set(), set()))
        self.true(FilterByTagsMixin.should_run(set(), {'a'}, set(), {'a'}, set()))
        self.true(FilterByTagsMixin.should_run({'a', 'b'}, set(), set(), set(), set()))
        self.true(FilterByTagsMixin.should_run({'a', 'b'}, set(), set(), set(), {'c', 'd'}))
        self.false(FilterByTagsMixin.should_run({'a', 'b'}, set(), set(), set(), {'c', 'b'}))
        self.true(FilterByTagsMixin.should_run({'a', 'b'}, set(), set(), {'c', 'a'}, set()))
        self.true(FilterByTagsMixin.should_run({'a', 'b'}, {'c', 'd'}, set(), {'c', 'a'}, set()))
        self.true(FilterByTagsMixin.should_run({'a', 'b'}, set(), set(), {'a'}, {'c', 'd'}))
        self.false(FilterByTagsMixin.should_run({'a', 'b'}, set(), set(), {'b'}, {'b'}))

    def test_should_run_with_extra(self):
        self.true(FilterByTagsMixin.should_run(set(), set(), {'a'}, set(), set()))
        self.true(FilterByTagsMixin.should_run(set(), set(), {'a'}, set(), {'b'}))
        self.false(FilterByTagsMixin.should_run(set(), set(), {'a'}, {'a'}, set()))
        self.false(FilterByTagsMixin.should_run(set(), set(), {'a'}, {'a'}, {'b'}))
        self.true(FilterByTagsMixin.should_run(set(), {'a'}, {'a'}, set(), set()))
        self.true(FilterByTagsMixin.should_run(set(), {'a'}, {'a'}, {'a'}, set()))
        self.true(FilterByTagsMixin.should_run({'a', 'b'}, set(), {'a'}, set(), set()))
        self.true(FilterByTagsMixin.should_run({'a', 'b'}, set(), {'a'}, set(), {'c', 'd'}))
        self.false(FilterByTagsMixin.should_run({'a', 'b'}, set(), {'a'}, set(), {'c', 'b'}))
        self.true(FilterByTagsMixin.should_run({'a', 'b'}, set(), {'a'}, {'c', 'a'}, set()))
        self.true(FilterByTagsMixin.should_run({'a', 'b'}, {'c', 'd'}, {'a'}, {'c', 'a'}, set()))
        self.true(FilterByTagsMixin.should_run({'a', 'b'}, set(), {'a'}, {'a'}, {'c', 'd'}))
        self.false(FilterByTagsMixin.should_run({'a', 'b'}, set(), {'a'}, {'b'}, {'b'}))

    def test_fast_class_skip(self):

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

        def test(counter, skip, extra_tags=None, only_tags=None, skip_tags=None):
            skipped = False
            try:
                TestCaseWithTags.extra_tags = extra_tags or set()
                TestCaseWithTags.only_tags = only_tags or set()
                TestCaseWithTags.skip_tags = skip_tags or set()
                TestCaseWithTags.fast_class_skip()
            except unittest.SkipTest:
                skipped = True
            msg = []
            for n, m in TestCaseWithTags.get_test_methods():
                args = (
                    TestCaseWithTags.get_tags(m), TestCaseWithTags.get_required_tags(m),
                    TestCaseWithTags.get_extra_tags(), TestCaseWithTags.get_only_tags(),
                    TestCaseWithTags.get_skip_tags()
                )
                msg.append([counter, n, TestCaseWithTags.should_run(*args), args])
            self.equal(skipped, skip, msg=msg)

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
    def test_with_tags_decorator(self):
        raise RuntimeError('This test should never run.')


class TestMissingMixin(base.TestCase):

    tags = ('unittest', )

    def test_is_missing(self):
        self.is_missing(Missing, 'Something bad happened')

    def test_is_not_missing(self):
        self.is_not_missing(None, 'Something bad happened')


class TestSnakeCaseMixin(base.TestCase):

    tags = ('unittest', )

    def test_getattr(self):
        asserts.equal(10, 10)
        with self.raises(AssertionError):
            asserts.equal(10, 2)
        asserts.dict_equal({}, {})
        with self.raises(AssertionError):
            asserts.dict_equal({}, {'a': 'b'})
