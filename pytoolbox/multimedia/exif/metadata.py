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

from . import tag
from ... import module
from ...encoding import string_types

_all = module.All(globals())


class Metadata(object):

    tag_class = tag.Tag

    def __init__(self, path):
        from gi.repository import GExiv2
        self.exiv2 = GExiv2.Metadata()
        self.exiv2.open_path(path)

    def __getitem__(self, key):
        return self.tag_class(self, key)

    @property
    def exposure_time(self):
        return self.exiv2.get_exposure_time()

    @property
    def tags(self):
        get = self.get
        return {k: get(k) for k in self.exiv2.get_tags()}

    def get(self, key):
        return self.tag_class(self, key)

    def get_date(self, keys=['Exif.Photo.DateTimeOriginal', 'Exif.Image.DateTime'], fail=True):
        for key in ([keys] if isinstance(keys, string_types) else keys):
            date = self.get(key).data_date(fail=fail)
            if date:
                return date

__all__ = _all.diff(globals())
