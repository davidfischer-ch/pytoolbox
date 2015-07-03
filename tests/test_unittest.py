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

from pytoolbox.unittest import asserts, with_tags, FilterByTagsMixin
from pytoolbox.types import Missing

from . import base


class TestFilterByTagsMixin(base.TestCase):

    tags = ('unittest', )

    def test_should_run(self):
        self.true(FilterByTagsMixin().should_run(set(), set(), set(), set()))
        self.true(FilterByTagsMixin().should_run(set(), set(), set(), {'b'}))
        self.false(FilterByTagsMixin().should_run(set(), set(), {'a'}, set()))
        self.false(FilterByTagsMixin().should_run(set(), set(), {'a'}, {'b'}))
        self.false(FilterByTagsMixin().should_run(set(), {'a'}, set(), set()))
        self.true(FilterByTagsMixin().should_run(set(), {'a'}, {'a'}, set()))
        self.true(FilterByTagsMixin().should_run({'a', 'b'}, set(), set(), set()))
        self.true(FilterByTagsMixin().should_run({'a', 'b'}, set(), set(), {'c', 'd'}))
        self.false(FilterByTagsMixin().should_run({'a', 'b'}, set(), set(), {'c', 'b'}))
        self.true(FilterByTagsMixin().should_run({'a', 'b'}, set(), {'c', 'a'}, set()))
        self.true(FilterByTagsMixin().should_run({'a', 'b'}, {'c', 'd'}, {'c', 'a'}, set()))
        self.true(FilterByTagsMixin().should_run({'a', 'b'}, set(), {'a'}, {'c', 'd'}))
        self.false(FilterByTagsMixin().should_run({'a', 'b'}, set(), {'b'}, {'b'}))

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
