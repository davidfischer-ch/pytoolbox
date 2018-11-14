# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox import collections, module

_all = module.All(globals())


class Brand(object):

    brands = frozenset([
        'Apple', 'Asus', 'Canon', 'Fujifilm', 'HP', 'HTC', 'GoPro', 'Hewlett-Packard', 'Kodak',
        'LGE', 'Nikon', 'Olympus', 'Pentax', 'Samsung', 'Sigma', 'Sony', 'Sony Ericsson'
    ])
    clean_map = collections.merge_dicts({b.lower(): b for b in brands}, {
        # maps the group of Exif.Group.Label
        'canoncs': 'Canon',
        'canoncf': 'Canon',
        'lg electronics': 'LGE',
        'nikon3': 'Nikon',
        'nikonld2': 'Nikon',
        'nikonld3': 'Nikon',
        'olympus2': 'Olympus',
        'sony1': 'Sony',
        # maps the value of Exif.Image.Make
        'eastman kodak company': 'Kodak',
        'nikon corporation': 'Nikon',
        'olympus imaging corp.': 'Olympus',
        'olympus optical co.,ltd': 'Olympus',
        'samsung techwin': 'Samsung',
        'semc': 'Sony Ericsson'
    })

    def __new__(cls, brand):
        return cls.clean(brand)

    @classmethod
    def clean(cls, brand):
        brand = brand.strip() if brand else brand
        if brand:
            brand = cls.clean_map.get(brand.lower(), brand)
            assert brand in cls.brands, 'Brand {1} not in {0.brands}'.format(cls, brand)
            return brand


__all__ = _all.diff(globals())
