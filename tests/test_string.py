# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox import string

from . import base


class TestString(base.TestCase):

    tags = ('string', )

    def test_camel_to_dash(self):
        self.equal(string.camel_to_dash('snakesOnAPlane'), 'snakes-on-a-plane')
        self.equal(string.camel_to_dash('SnakesOnAPlane'), 'snakes-on-a-plane')
        self.equal(string.camel_to_dash('-Snakes-On-APlane-'), '-snakes-on-a-plane-')
        self.equal(string.camel_to_dash('snakes-on-a-plane'), 'snakes-on-a-plane')
        self.equal(string.camel_to_dash('IPhoneHysteria'), 'i-phone-hysteria')
        self.equal(string.camel_to_dash('iPhoneHysteria'), 'i-phone-hysteria')
        self.equal(string.camel_to_dash('iPHONEHysteria'), 'i-phone-hysteria')
        self.equal(string.camel_to_dash('-iPHONEHysteria'), '-i-phone-hysteria')
        self.equal(string.camel_to_dash('iPHONEHysteria-'), 'i-phone-hysteria-')

    def test_camel_to_snake(self):
        self.equal(string.camel_to_snake('snakesOnAPlane'), 'snakes_on_a_plane')
        self.equal(string.camel_to_snake('SnakesOnAPlane'), 'snakes_on_a_plane')
        self.equal(string.camel_to_snake('_Snakes_On_APlane_'), '_snakes_on_a_plane_')
        self.equal(string.camel_to_snake('snakes_on_a_plane'), 'snakes_on_a_plane')
        self.equal(string.camel_to_snake('IPhoneHysteria'), 'i_phone_hysteria')
        self.equal(string.camel_to_snake('iPhoneHysteria'), 'i_phone_hysteria')
        self.equal(string.camel_to_snake('iPHONEHysteria'), 'i_phone_hysteria')
        self.equal(string.camel_to_snake('_iPHONEHysteria'), '_i_phone_hysteria')
        self.equal(string.camel_to_snake('iPHONEHysteria_'), 'i_phone_hysteria_')

    def test_dash_to_camel(self):
        self.equal(string.dash_to_camel('-snakes-on-a-plane-'), '-snakesOnAPlane-')
        self.equal(string.dash_to_camel('snakes-on-a-plane'), 'snakesOnAPlane')
        self.equal(string.dash_to_camel('Snakes-on-a-plane'), 'snakesOnAPlane')
        self.equal(string.dash_to_camel('snakesOnAPlane'), 'snakesOnAPlane')
        self.equal(string.dash_to_camel('I-phone-hysteria'), 'iPhoneHysteria')
        self.equal(string.dash_to_camel('i-phone-hysteria'), 'iPhoneHysteria')
        self.equal(string.dash_to_camel('i-PHONE-hysteria'), 'iPHONEHysteria')
        self.equal(string.dash_to_camel('-i-phone-hysteria'), '-iPhoneHysteria')
        self.equal(string.dash_to_camel('i-phone-hysteria-'), 'iPhoneHysteria-')

    def test_snake_to_camel(self):
        self.equal(string.snake_to_camel('_snakes_on_a_plane_'), '_snakesOnAPlane_')
        self.equal(string.snake_to_camel('snakes_on_a_plane'), 'snakesOnAPlane')
        self.equal(string.snake_to_camel('Snakes_on_a_plane'), 'snakesOnAPlane')
        self.equal(string.snake_to_camel('snakesOnAPlane'), 'snakesOnAPlane')
        self.equal(string.snake_to_camel('I_phone_hysteria'), 'iPhoneHysteria')
        self.equal(string.snake_to_camel('i_phone_hysteria'), 'iPhoneHysteria')
        self.equal(string.snake_to_camel('i_PHONE_hysteria'), 'iPHONEHysteria')
        self.equal(string.snake_to_camel('_i_phone_hysteria'), '_iPhoneHysteria')
        self.equal(string.snake_to_camel('i_phone_hysteria_'), 'iPhoneHysteria_')
