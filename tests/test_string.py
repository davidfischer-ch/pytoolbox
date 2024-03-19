from __future__ import annotations

from pytoolbox import string


def test_camel_to_dash() -> None:
    assert string.camel_to_dash('snakesOnAPlane') == 'snakes-on-a-plane'
    assert string.camel_to_dash('SnakesOnAPlane') == 'snakes-on-a-plane'
    assert string.camel_to_dash('-Snakes-On-APlane-') == '-snakes-on-a-plane-'
    assert string.camel_to_dash('snakes-on-a-plane') == 'snakes-on-a-plane'
    assert string.camel_to_dash('IPhoneHysteria') == 'i-phone-hysteria'
    assert string.camel_to_dash('iPhoneHysteria') == 'i-phone-hysteria'
    assert string.camel_to_dash('iPHONEHysteria') == 'i-phone-hysteria'
    assert string.camel_to_dash('-iPHONEHysteria') == '-i-phone-hysteria'
    assert string.camel_to_dash('iPHONEHysteria-') == 'i-phone-hysteria-'


def test_camel_to_snake() -> None:
    assert string.camel_to_snake('snakesOnAPlane') == 'snakes_on_a_plane'
    assert string.camel_to_snake('SnakesOnAPlane') == 'snakes_on_a_plane'
    assert string.camel_to_snake('_Snakes_On_APlane_') == '_snakes_on_a_plane_'
    assert string.camel_to_snake('snakes_on_a_plane') == 'snakes_on_a_plane'
    assert string.camel_to_snake('IPhoneHysteria') == 'i_phone_hysteria'
    assert string.camel_to_snake('iPhoneHysteria') == 'i_phone_hysteria'
    assert string.camel_to_snake('iPHONEHysteria') == 'i_phone_hysteria'
    assert string.camel_to_snake('_iPHONEHysteria') == '_i_phone_hysteria'
    assert string.camel_to_snake('iPHONEHysteria_') == 'i_phone_hysteria_'


def test_dash_to_camel() -> None:
    assert string.dash_to_camel('-snakes-on-a-plane-') == '-snakesOnAPlane-'
    assert string.dash_to_camel('snakes-on-a-plane') == 'snakesOnAPlane'
    assert string.dash_to_camel('Snakes-on-a-plane') == 'snakesOnAPlane'
    assert string.dash_to_camel('snakesOnAPlane') == 'snakesOnAPlane'
    assert string.dash_to_camel('I-phone-hysteria') == 'iPhoneHysteria'
    assert string.dash_to_camel('i-phone-hysteria') == 'iPhoneHysteria'
    assert string.dash_to_camel('i-PHONE-hysteria') == 'iPHONEHysteria'
    assert string.dash_to_camel('-i-phone-hysteria') == '-iPhoneHysteria'
    assert string.dash_to_camel('i-phone-hysteria-') == 'iPhoneHysteria-'


def test_snake_to_camel() -> None:
    assert string.snake_to_camel('_snakes_on_a_plane_') == '_snakesOnAPlane_'
    assert string.snake_to_camel('snakes_on_a_plane') == 'snakesOnAPlane'
    assert string.snake_to_camel('Snakes_on_a_plane') == 'snakesOnAPlane'
    assert string.snake_to_camel('snakesOnAPlane') == 'snakesOnAPlane'
    assert string.snake_to_camel('I_phone_hysteria') == 'iPhoneHysteria'
    assert string.snake_to_camel('i_phone_hysteria') == 'iPhoneHysteria'
    assert string.snake_to_camel('i_PHONE_hysteria') == 'iPHONEHysteria'
    assert string.snake_to_camel('_i_phone_hysteria') == '_iPhoneHysteria'
    assert string.snake_to_camel('i_phone_hysteria_') == 'iPhoneHysteria_'
