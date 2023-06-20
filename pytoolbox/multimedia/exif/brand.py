from __future__ import annotations

from pytoolbox import collections, exceptions

__all__ = ['Brand']


class Brand(object):

    brands = frozenset([
        'Apple',
        'Asus',
        'Canon',
        'Fujifilm',
        'HP',
        'HTC',
        'Huawei',
        'GoPro',
        'Hewlett-Packard',
        'Kodak',
        'LGE',
        'Nikon',
        'Olympus',
        'Pentax',
        'Samsung',
        'Sigma',
        'Sony',
        'Sony Ericsson',
        'Tamron'
    ])

    clean_map = collections.merge_dicts({b.lower(): b for b in brands}, {
        # maps the group of Exif.Group.Label
        'canoncs': 'Canon',
        'canoncf': 'Canon',
        'HUAWEI': 'Huawei',
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
        'semc': 'Sony Ericsson',
        'tamron': 'Tamron'
    })

    def __new__(cls, brand: str):
        return cls.clean(brand)

    @classmethod
    def clean(cls, brand: str) -> str | None:
        brand = brand.strip() if brand else brand
        if not brand:  # pylint:disable=consider-using-assignment-expr
            return None
        if (brand := cls.clean_map.get(brand.lower(), brand)) not in cls.brands:
            raise exceptions.InvalidBrandError(brand=brand, brands=cls.brands)
        return brand
