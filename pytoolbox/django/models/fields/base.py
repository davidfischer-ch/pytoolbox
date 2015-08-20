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

from django.db import models
from django.utils.timezone import now

from . import mixins
from .... import module

_all = module.All(globals())


# Char & Text

class StripCharField(mixins.StripMixin, models.CharField):
    pass


class StripTextField(mixins.StripMixin, models.TextField):
    pass


class ExtraChoicesField(StripCharField):

    def __init__(self, verbose_name=None, extra_choices=None, **kwargs):
        self.extra_choices = extra_choices or []
        super(ExtraChoicesField, self).__init__(verbose_name=verbose_name, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(ExtraChoicesField, self).deconstruct()
        if self.extra_choices:
            kwargs['extra_choices'] = self.extra_choices
        return name, path, args, kwargs

    def validate(self, value, model_instance):
        choices = self._choices
        try:
            self._choices = list(self.choices) + list(self.extra_choices)
            return super(ExtraChoicesField, self).validate(value, model_instance)
        finally:
            self._choices = choices


# Date and time

class CreatedAtField(models.DateTimeField):

    def __init__(self, default=now, editable=False, **kwargs):
        super(CreatedAtField, self).__init__(default=default, editable=editable, **kwargs)


class UpdatedAtField(models.DateTimeField):

    def __init__(self, auto_now=True, editable=False, **kwargs):
        super(UpdatedAtField, self).__init__(auto_now=auto_now, editable=editable, **kwargs)


# Miscellaneous

class URLField(StripCharField, models.URLField):

    # http://tools.ietf.org/html/rfc7230#section-3.1.1
    def __init__(self, max_length=8000, **kwargs):
        super(URLField, self).__init__(max_length=max_length, **kwargs)

__all__ = _all.diff(globals())
