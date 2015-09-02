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

from ... import collections, module

_all = module.All(globals())


class Brand(object):

    brands = frozenset([
        'Apple', 'Asus', 'Canon', 'Fujifilm', 'HP', 'HTC', 'GoPro', 'Kodak', 'LGE', 'Nikon', 'Olympus', 'Pentax',
        'Samsung', 'Sigma', 'Sony', 'Sony Ericsson'
    ])
    clean_map = collections.merge_dicts({b.lower(): b for b in brands}, {
        # maps the group of Exif.Group.Label
        'canoncs': 'Canon',
        'canoncf': 'Canon',
        'nikon3': 'Nikon',
        'nikonld2': 'Nikon',
        'nikonld3': 'Nikon',
        'olympus2': 'Olympus',
        'sony1': 'Sony',
        # maps the value of Exif.Image.Make
        'eastman kodak company': 'Kodak',
        'nikon corporation': 'Nikon',
        'olympus imaging corp.': 'Olympus',
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
