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

from django.contrib.contenttypes import models as ct_models

__all__ = ('get_base_model', 'get_content_type_dict', 'get_instance')


def get_base_model(cls_or_instance):
    return cls_or_instance._meta.proxy_for_model or cls_or_instance._meta.model


def get_content_type_dict(instance):
    """Return a dictionary with the serialized content type and private key of given instance."""
    content_type = ct_models.ContentType.objects.get_for_model(instance.__class__)
    return {'app_label': content_type.app_label, 'model': content_type.model, 'pk': instance.pk}


def get_instance(app_label, model, pk):
    """Return an instance given its app_label, model name and private key."""
    return ct_models.ContentType.objects.get(app_label=app_label, model=model).get_object_for_this_type(pk=pk)
