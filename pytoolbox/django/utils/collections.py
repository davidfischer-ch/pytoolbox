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

from ..constants import DEFFERED_REGEX
from ... import module

_all = module.All(globals())


class FieldsToValuesLookupDict(object):
    """
    Global registry for mapping X class fields to W values.

    * X can be a Model, a (Model)Form, a REST Framework Serializer, ...
    * Y can be the fields help texts or verbose names, or the number 42.

    Strange idea? Isn't it?

    Here is a short example as an appetizer. Suppose you want to define your application's help texts into a centralized
    registry, for keeping your wording DRY. And suppose you have some models like this:

    >> class Media(models.Model):
    ..     url = models.URLField()

    >> class File(models.Model):
    ..     url = models.URLField()

    And you instantiate this class with:

    >> help_texts = FieldsLookupDict({'Media.url': 'The media asset ingest URL', 'url': 'An URL'})

    Then, you can lookup for the help text of a field like this:

    >> help_texts[(Media, 'url')]
    The media asset ingest URL

    >> help_texts[(File, 'url')]
    An URL

    The value returned will be the first matching to the following keys:

    1. '<cls.__name__>.<field_name>'
    2. '<field_name>'

    If given class have a _meta or Meta ("meta") attribute with a model attribute, then the following keys are tried:

    1. '<cls.__name__>.<field_name>'
    2. '<cls._meta.model>.<field_name>'
    3. '<field_name>'
    """

    def __init__(self, name, translations=None):
        self.name = name
        self.translations = translations or {}

    def __getitem__(self, key):
        if isinstance(key, str):
            keys = [key]
        else:
            cls, field_name = key
            keys = ['{0.__name__}.{1}'.format(cls, field_name), field_name]
            meta = getattr(cls, '_meta', None) or getattr(cls, 'Meta', None)
            if meta and hasattr(meta, 'model'):
                # cleanup model name when some fields are deferred (Media vs Media_Deffered_...)
                keys.insert(1, '{0}.{1}'.format(DEFFERED_REGEX.sub('', meta.model.__name__), field_name))
        for key in keys:
            value = self.translations.get(key)
            if value:
                return value
        raise KeyError('Entry for keys {1} not found in {0.name}.'.format(self, keys))

    def __setitem__(self, key, value):
        self.translations[key] = value

__all__ = _all.diff(globals())
