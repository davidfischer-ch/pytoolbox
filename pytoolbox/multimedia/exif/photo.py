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

import inspect
try:
    from ...enum import OrderedEnum

    class ExposureMode(OrderedEnum):
        AUTO = 0
        MANUAL = 1
        BRACKET = 2

    class Orientation(OrderedEnum):
        NORMAL = 1
        HOR_FLIP = 2
        ROT_180_CCW = 3
        VERT_FLIP = 4
        HOR_FLIP_ROT_270_CW = 5
        ROT_90_CW = 6
        HOR_FLIP_ROT_90_CW = 7
        ROT_270_CW = 8

except ImportError:
    ExposureMode = {0: 'auto', 1: 'manual', 2: 'bracket'}.get
    Orientation = lambda x: range(1, 9)[x-1]

from ... import module

_all = module.All(globals())


class Photo(object):
    # FIXME split into more classes to categorize?
    # Example: optical settings vs image file properties

    @staticmethod
    def clean_number(number):
        return number if number and number > 0 else None

    def __init__(self, metadata):
        self.metadata = metadata

    @property
    def copyright(self):
        return self.metadata['Iptc.Application2.Copyright'].data

    @property
    def date(self):
        return self.metadata.get_date()

    @property
    def description(self):
        return self.metadata['Exif.Image.ImageDescription'].data

    @property
    def exposure_mode(self):
        return ExposureMode(self.metadata['Exif.Photo.ExposureMode'].data)

    @property
    def exposure_time(self):
        return self.metadata.exiv2.get_exposure_time() or None

    @property
    def fnumber(self):
        return self.clean_number(self.metadata['Exif.Image.FNumber'].data)

    @property
    def focal_length(self):
        return self.clean_number(self.metadata['Exif.Image.FocalLength'].data)

    @property
    def height(self):
        return self.metadata.exiv2.get_pixel_height() or None

    @property
    def iso(self):
        return self.metadata['Exif.Photo.ISOSpeed'].data or None

    @property
    def orientation(self):
        data = self.metadata['Exif.Image.Orientation'].data
        try:
            return Orientation(data)
        except:
            return None

    @property
    def sensing_method(self):
        return self.metadata['Exif.Photo.SensingMethod'].data

    @property
    def white_balance(self):
        return self.metadata['Exif.Photo.WhiteBalance'].data

    @property
    def width(self):
        return self.metadata.exiv2.get_pixel_width() or None

    def properties(self):
        return ((n, getattr(self, n)) for n, p in inspect.getmembers(self.__class__, lambda m: isinstance(m, property)))

__all__ = _all.diff(globals())
