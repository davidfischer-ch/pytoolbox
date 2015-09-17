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

from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _

from ... import module
from ...django.models import utils

_all = module.All(globals())


class BaseModelMixin(object):

    def build_url_field(self, field_name, model_class):
        return super(BaseModelMixin, self).build_url_field(field_name, utils.get_base_model(model_class))


class FromPrivateKeyMixin(object):
    """Allow to provide the PK of the model to retrieve it instead of creating a new instance with fields from data."""

    default_error_messages = {
        'does_not_exist': _("Invalid pk '%s' - object does not exist."),
        'incorrect_type': _('Incorrect type. Expected pk value, received %s.'),
    }

    def to_internal_value(self, data):
        """Transform the *incoming* primitive data into a native value."""
        if not data or isinstance(data, dict):
            return super(FromPrivateKeyMixin, self).to_internal_value(data)
        try:
            return self.Meta.model.objects.get(pk=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', smart_text(data))
        except (TypeError, ValueError):
            self.fail('incorrect_type', type(data).__name__)

    def create(self, validated_data):
        if isinstance(validated_data, self.Meta.model):
            return validated_data
        return super(FromPrivateKeyMixin, self).create(validated_data)


class NestedCreateMixin(object):

    def to_internal_value(self, data):
        """Return a tuple with (self, validate_data) to allow working on validated data with this serializer."""
        return self, super(NestedCreateMixin, self).to_internal_value(data)


class NestedUpdateMixin(object):

    def to_internal_value(self, data):
        """Return a tuple with (self, validate_data) to allow working on validated data with this serializer."""
        return self, super(NestedUpdateMixin, self).to_internal_value(data)


class ReadOnlyMixin(object):

    def __init__(self, *args, **kwargs):
        kwargs['read_only'] = True
        super(ReadOnlyMixin, self).__init__(*args, **kwargs)

__all__ = _all.diff(globals())
