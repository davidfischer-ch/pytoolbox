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

import nose, os, sys, time, unittest
from os.path import abspath, dirname

if sys.version_info[0] > 2:
    from unittest.mock import Mock
else:
    from mock import Mock

__all__ = (
    'Mock', 'MOCK_SIDE_EFFECT_RETURNS', 'mock_cmd', 'mock_side_effect', 'runtests', 'AwareTearDownMixin',
    'TimingMixin'
)

MOCK_SIDE_EFFECT_RETURNS = [Exception('you must set MOCK_SIDE_EFFECT_RETURNS'), {'title': '2nd'}]


def mock_cmd(stdout='', stderr='', returncode=0):
    return Mock(return_value={'stdout': stdout, 'stderr': stderr, 'returncode': returncode})


def mock_side_effect(*args, **kwargs):
    """
    Pop and return values from MOCK_SIDE_EFFECT_RETURNS.

    From your own module, you need to set MOCK_SIDE_EFFECT_RETURNS before using this function::

        import pytoolbox.unittest
        pytoolbox.unittest.MOCK_SIDE_EFFECT_RETURNS = ['1st', {'title': '2nd'}, EOFError('last')]

    **example usage**

    Set content (only required for this doctest, see previous remark):

    Pops return values with `mock_side_effect`:

    >>> from nose.tools import eq_
    >>>
    >>> print(mock_side_effect())
    Traceback (most recent call last):
    ...
    Exception: you must set MOCK_SIDE_EFFECT_RETURNS
    >>> eq_(mock_side_effect(), {'title': '2nd'})
    >>>
    >>> print(mock_side_effect())
    Traceback (most recent call last):
    ...
    IndexError: pop from empty list
    """
    global MOCK_SIDE_EFFECT_RETURNS
    result = MOCK_SIDE_EFFECT_RETURNS.pop(0)
    if isinstance(result, Exception):
        raise result
    return result


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
        result = super().run(result)
        self.awareTearDown(result)
        return result


class FilterByTagsMixin(object):

    tags = ()
    only_tags_variable = 'TEST_ONLY_TAGS'
    skip_tags_variable = 'TEST_SKIP_TAGS'

    @classmethod
    def get_tags(cls):
        return cls.tags

    @classmethod
    def get_only_tags(cls):
        return [t for t in os.environ.get(cls.only_tags_variable, '').split(',') if t]

    @classmethod
    def get_skip_tags(cls):
        return [t for t in os.environ.get(cls.skip_tags_variable, '').split(',') if t]

    @staticmethod
    def should_run(tags, only_tags, skip_tags):
        tags = frozenset(tags or [])
        only_tags = frozenset(only_tags or [])
        skip_tags = frozenset(skip_tags or [])
        return not tags & skip_tags and (bool(tags & only_tags) if tags and only_tags else True)

    @classmethod
    def setUpClass(cls):
        if not cls.should_run(cls.get_tags(), cls.get_only_tags(), cls.get_skip_tags()):
            raise unittest.SkipTest('Test skipped by FilterByTagsMixin')
        super(FilterByTagsMixin, cls).setUpClass()


class TimingMixin(object):

    timing_logger = None

    def setUp(self):
        self.start_time = time.time()
        super(TimingMixin, self).setUp()

    def tearDown(self):
        super(TimingMixin, self).tearDown()
        if self.timing_logger:
            self.timing_logger.info('{0}: {1:.3f}'.format(self.id(), time.time() - self.start_time))
