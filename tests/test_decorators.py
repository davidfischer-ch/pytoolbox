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
from pytoolbox import decorators
from pytoolbox.unittest import FilterByTagsMixin


class TestDecorators(FilterByTagsMixin, unittest.TestCase):

    tags = ('decorators', )

    def test_run_once(self):

        @decorators.run_once
        def increment(counter):
            return counter + 1

        @decorators.run_once
        def decrement(counter):
            return counter - 1

        self.assertEqual(increment(0), 1)
        self.assertIsNone(increment(0))
        self.assertEqual(decrement(1), 0)
        self.assertIsNone(decrement(0))
        increment.executed = False
        self.assertEqual(increment(5.5), 6.5)
        self.assertIsNone(increment(5.5))
