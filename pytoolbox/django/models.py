# -*- coding: utf-8 -*-

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

from django.core.urlresolvers import reverse
from django.db.models.fields.files import FileField


class AbsoluteUrlMixin(object):
    """
    Implement get_absolute_url based on the convention that the views URLs are based on the lower-case model's name.
    """
    # https://docs.djangoproject.com/en/dev/topics/class-based-views/generic-editing/
    def get_absolute_url(self, suffix=None):
        return reverse('{0}_{1}'.format(self.__class__.__name__.lower(),
                       suffix or ('update' if self.pk else 'create')),
                       kwargs={'pk': self.pk} if self.pk else None)


class SaveInstanceFilesMixin(object):
    """
    Overrides saves() with a method that saves the instance first and then the instance's file fields this ensure
    that the upload_path method will get a valid instance id / private key.
    """
    def save(self, *args, **kwargs):
        saved_fields = {}
        if self.id is None:
            for field in self._meta.fields:
                if isinstance(field, FileField):
                    saved_fields[field.name] = getattr(self, field.name)
                    setattr(self, field.name, None)
            super(SaveInstanceFilesMixin, self).save(*args, **kwargs)
            for name, value in saved_fields.iteritems():
                setattr(self, name, value)
        super(SaveInstanceFilesMixin, self).save(*args, **kwargs)
