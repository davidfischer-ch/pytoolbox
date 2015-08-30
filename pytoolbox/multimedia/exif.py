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

import logging
from datetime import datetime
from fractions import Fraction

from .. import decorators, module
from ..datetime import str_to_datetime
from ..encoding import string_types

_all = module.All(globals())
logger = logging.getLogger(__name__)


class Tag(object):

    type_to_hook = {
        Fraction: 'get_exif_tag_rational',
        int: 'get_tag_long',
        list: 'get_tag_multiple',
        str: 'get_tag_string'
    }
    type_to_python = {
        'Ascii': str,
        'Byte': bytes,
        'Comment': str,
        'Long': int,
        'SLong': int,
        'Short': int,
        'SShort': int,
        'String': str,
        'Rational': Fraction,
        'SRational': Fraction,
        'Undefined': bytes,
        'XmpSeq': list,
        'XmpText': str
    }

    def __init__(self, metadata, key):
        """Metadata should be an instance of :class:`GExiv2.Metadata`."""
        self.metadata = metadata
        self.key = key

    def __repr__(self):
        return '<{0.__class__} {0.key}: {1}>'.format(self, str(self.data)[:20])

    @property
    def data(self):
        type_hook = self.get_type_hook()
        if type_hook:
            try:
                data = type_hook(self.key)
            except UnicodeDecodeError as e:
                return e
            return (str_to_datetime(data, fail=False) or data) if isinstance(data, string_types) and ':' in data else data
        return self.data_bytes

    @property
    def data_bytes(self):
        return self.metadata.get_tag_raw(self.key).get_data()

    @decorators.cached_property
    def description(self):
        return self.metadata.get_tag_description(self.key)

    @decorators.cached_property
    def label(self):
        return self.metadata.get_tag_label(self.key)

    @property
    def size(self):
        return self.metadata.get_tag_raw(self.key).get_size()

    @decorators.cached_property
    def type(self):
        return self.type_to_python[self.metadata.get_tag_type(self.key)]

    def get_type_hook(self):
        name = self.type_to_hook.get(self.type)
        return getattr(self.metadata, name) if name else None


class Metadata(object):

    tag_class = Tag

    def __init__(self, path):
        from gi.repository import GExiv2
        self._m = GExiv2.Metadata()
        self._m.open_path(path)

    def __getitem__(self, key):
        return self.tag_class(self._m, key)

    @property
    def exposure_time(self):
        return self._m.get_exposure_time()

    @property
    def tags(self):
        get = self.get
        return {k: get(k) for k in self._m.get_tags()}

    def get(self, key):
        return self.tag_class(self._m, key)

    def get_date(self, keys=['Exif.Photo.DateTimeOriginal', 'Exif.Image.DateTime'], fail=True):
        for key in ([keys] if isinstance(keys, string_types) else keys):
            date = self.get(key).data_date(fail=fail)
            if date:
                return date

__all__ = _all.diff(globals())
