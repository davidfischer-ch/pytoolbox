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

import unittest
from pytoolbox.unittest import FilterByTagsMixin


class TestFilterByTagsMixin(FilterByTagsMixin, unittest.TestCase):

    tags = ('unittest', )

    def test_should_run(self):
        self.assertTrue(FilterByTagsMixin().should_run(set(), set(), set()))
        self.assertTrue(FilterByTagsMixin().should_run(set(), {'a'}, set()))
        self.assertTrue(FilterByTagsMixin().should_run(set(), set(), {'b'}))
        self.assertTrue(FilterByTagsMixin().should_run(set(), {'a'}, {'b'}))
        self.assertTrue(FilterByTagsMixin().should_run({'a', 'b'}, set(), set()))
        self.assertTrue(FilterByTagsMixin().should_run({'a', 'b'}, set(), {'c', 'd'}))
        self.assertFalse(FilterByTagsMixin().should_run({'a', 'b'}, set(), {'c', 'b'}))
        self.assertTrue(FilterByTagsMixin().should_run({'a', 'b'}, {'c', 'a'}, set()))
        self.assertTrue(FilterByTagsMixin().should_run({'a', 'b'}, {'a'}, {'c', 'd'}))
        self.assertFalse(FilterByTagsMixin().should_run({'a', 'b'}, {'b'}, {'b'}))
