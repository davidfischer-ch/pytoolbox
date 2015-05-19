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
# Credits: https://gist.github.com/yahyaKacem/8170675
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division, print_function, unicode_literals

import unittest
from pytoolbox import string
from pytoolbox.unittest import FilterByTagsMixin


class TestString(FilterByTagsMixin, unittest.TestCase):

    tags = ('string', )

    def test_camel_to_dash(self):
        self.assertEqual(string.camel_to_dash('snakesOnAPlane'), 'snakes-on-a-plane')
        self.assertEqual(string.camel_to_dash('SnakesOnAPlane'), 'snakes-on-a-plane')
        self.assertEqual(string.camel_to_dash('-Snakes-On-APlane-'), '-snakes-on-a-plane-')
        self.assertEqual(string.camel_to_dash('snakes-on-a-plane'), 'snakes-on-a-plane')
        self.assertEqual(string.camel_to_dash('IPhoneHysteria'), 'i-phone-hysteria')
        self.assertEqual(string.camel_to_dash('iPhoneHysteria'), 'i-phone-hysteria')
        self.assertEqual(string.camel_to_dash('iPHONEHysteria'), 'i-phone-hysteria')
        self.assertEqual(string.camel_to_dash('-iPHONEHysteria'), '-i-phone-hysteria')
        self.assertEqual(string.camel_to_dash('iPHONEHysteria-'), 'i-phone-hysteria-')

    def test_camel_to_snake(self):
        self.assertEqual(string.camel_to_snake('snakesOnAPlane'), 'snakes_on_a_plane')
        self.assertEqual(string.camel_to_snake('SnakesOnAPlane'), 'snakes_on_a_plane')
        self.assertEqual(string.camel_to_snake('_Snakes_On_APlane_'), '_snakes_on_a_plane_')
        self.assertEqual(string.camel_to_snake('snakes_on_a_plane'), 'snakes_on_a_plane')
        self.assertEqual(string.camel_to_snake('IPhoneHysteria'), 'i_phone_hysteria')
        self.assertEqual(string.camel_to_snake('iPhoneHysteria'), 'i_phone_hysteria')
        self.assertEqual(string.camel_to_snake('iPHONEHysteria'), 'i_phone_hysteria')
        self.assertEqual(string.camel_to_snake('_iPHONEHysteria'), '_i_phone_hysteria')
        self.assertEqual(string.camel_to_snake('iPHONEHysteria_'), 'i_phone_hysteria_')

    def test_dash_to_camel(self):
        self.assertEqual(string.dash_to_camel('-snakes-on-a-plane-'), '-snakesOnAPlane-')
        self.assertEqual(string.dash_to_camel('snakes-on-a-plane'), 'snakesOnAPlane')
        self.assertEqual(string.dash_to_camel('Snakes-on-a-plane'), 'snakesOnAPlane')
        self.assertEqual(string.dash_to_camel('snakesOnAPlane'), 'snakesOnAPlane')
        self.assertEqual(string.dash_to_camel('I-phone-hysteria'), 'iPhoneHysteria')
        self.assertEqual(string.dash_to_camel('i-phone-hysteria'), 'iPhoneHysteria')
        self.assertEqual(string.dash_to_camel('i-PHONE-hysteria'), 'iPHONEHysteria')
        self.assertEqual(string.dash_to_camel('-i-phone-hysteria'), '-iPhoneHysteria')
        self.assertEqual(string.dash_to_camel('i-phone-hysteria-'), 'iPhoneHysteria-')

    def test_snake_to_camel(self):
        self.assertEqual(string.snake_to_camel('_snakes_on_a_plane_'), '_snakesOnAPlane_')
        self.assertEqual(string.snake_to_camel('snakes_on_a_plane'), 'snakesOnAPlane')
        self.assertEqual(string.snake_to_camel('Snakes_on_a_plane'), 'snakesOnAPlane')
        self.assertEqual(string.snake_to_camel('snakesOnAPlane'), 'snakesOnAPlane')
        self.assertEqual(string.snake_to_camel('I_phone_hysteria'), 'iPhoneHysteria')
        self.assertEqual(string.snake_to_camel('i_phone_hysteria'), 'iPhoneHysteria')
        self.assertEqual(string.snake_to_camel('i_PHONE_hysteria'), 'iPHONEHysteria')
        self.assertEqual(string.snake_to_camel('_i_phone_hysteria'), '_iPhoneHysteria')
        self.assertEqual(string.snake_to_camel('i_phone_hysteria_'), 'iPhoneHysteria_')
