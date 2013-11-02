# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
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

import errno, os
from django.db.models.fields.files import FileField


def clean_files_delete_handler(instance, signal, **kwargs):
    u"""
    Remove the files of the instance's file fields when it is removed from the database.

    Simply use ``post_delete.connect(clean_files_delete_handler, sender=<your_model_class>)``

    .. warning:: This function remove the file without worrying about any other instance using this file !
    """
    for field in kwargs[u'sender']._meta.fields:
        if isinstance(field, FileField):
            try:
                filename = getattr(instance, field.name).path
                if filename:
                    os.remove(filename)
            except IOError as e:
                if e.errno != errno.ENOENT:
                    raise
