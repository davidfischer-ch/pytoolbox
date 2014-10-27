# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2014 David Fischer. All rights reserved.
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

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import ugettext_lazy as _
from rest_framework.compat import smart_text

__all__ = ('DisableValidateOnSaveMixin', 'FromPrivateKeyMixin')


class DisableValidateOnSaveMixin(object):
    """
    Disable call of obj.full_clean() by obj.save() because django-rest-framework views already calls it.
    For example, use it if your model inherit from :mod:`pytoolbox.django.models.mixins.ValidateOnSaveMixin`.
    """

    def save_object(self, obj, **kwargs):
        kwargs['validate'] = False
        return super(DisableValidateOnSaveMixin, self).save_object(obj, **kwargs)


class FromPrivateKeyMixin(object):
    """Allow to provide the PK of the model to retrieve it instead of creating a new instance with fields from data."""

    default_error_messages = {
        'does_not_exist': _("Invalid pk '%s' - object does not exist."),
        'incorrect_type': _('Incorrect type.  Expected pk value, received %s.'),
    }

    def from_native(self, data, files=None):
        if not data or isinstance(data, dict):
            return super().from_native(data, files)
        try:
            obj = self.opts.model.objects.get(pk=data)
            obj._from_pk = True
            return obj
        except ObjectDoesNotExist:
            raise ValidationError(self.error_messages['does_not_exist'] % smart_text(data))
        except (TypeError, ValueError):
            received = type(data).__name__
            raise ValidationError(self.error_messages['incorrect_type'] % received)

    def save_object(self, obj, **kwargs):
        if not getattr(obj, '_from_pk', False):
            obj.save(**kwargs)
