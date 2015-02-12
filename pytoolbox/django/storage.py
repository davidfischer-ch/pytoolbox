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

import logging, time
from django.core.files.storage import FileSystemStorage

__all__ = ('OverwriteMixin', 'OverwriteFileSystemStorage')

logger = logging.getLogger(__name__)


class ExpressTemporaryFileMixin(object):

    def _save(self, name, content):
        """
        Save the temporary file to the storage.
        Set temporary file path to allow using rename instead of chunked copy when possible.

        See what happens in super()._save(): https://github.com/django/django/blob/master/django/core/files/storage.py
        """
        start_time = time.time()
        if hasattr(content.file, 'temporary_file_path'):
            content.temporary_file_path = lambda: content.file.temporary_file_path()
        result = super(ExpressTemporaryFileMixin, self)._save(name, content)
        logger.debug('Saved protected file "{0}" in {1:.2g} seconds'.format(name, time.time() - start_time))
        return result


class OverwriteMixin(object):
    """Update get_available_name to remove any previously stored file (if any) before returning the name."""

    def get_available_name(self, name):
        self.delete(name)
        return name


class OverwriteFileSystemStorage(OverwriteMixin, FileSystemStorage):
    """A file-system based storage that let overwrite files with the same name."""
