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
from pytoolbox.validation import validate_list


class TestValidation(unittest.TestCase):

    def test_validate_list(self):
        regexes = [r'\d+', r"call\(\[u*'my_var', recursive=(True|False)\]\)"]
        validate_list([10, "call(['my_var', recursive=False])"], regexes)

    def test_validate_list_fail_size(self):
        with self.assertRaises(IndexError):
            validate_list([1, 2], [1, 2, 3])

    def test_validate_list_fail_value(self):
        with self.assertRaises(ValueError):
            regexes = [r'\d+', r"call\(\[u*'my_var', recursive=(True|False)\]\)"]
            validate_list([10, "call(['my_var', recursive='error'])"], regexes)
