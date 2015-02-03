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

import itertools, re
from django.core.exceptions import NON_FIELD_ERRORS
from django.core.urlresolvers import reverse
from django.db import DatabaseError
from django.db.models import FieldDoesNotExist
from django.db.models.fields.files import FileField
from django.db.utils import IntegrityError

from .. import exceptions

__all__ = (
    'AbsoluteUrlMixin', 'AlwaysUpdateFieldsMixin', 'AutoUpdateFieldsMixin', 'MapUniqueTogetherMixin',
    'MapUniqueTogetherIntegrityErrorToValidationErrorMixin', 'ReloadMixin', 'SaveInstanceFilesMixin',
    'UpdatePreconditionsMixin', 'ValidateOnSaveMixin'
)


class AbsoluteUrlMixin(object):
    """
    Implement get_absolute_url based on the convention that the views URLs are based on the lower-case model's name.
    """
    # https://docs.djangoproject.com/en/dev/topics/class-based-views/generic-editing/
    def get_absolute_url(self, suffix=None):
        return reverse('{0}_{1}'.format(self.__class__.__name__.lower(),
                       suffix or ('update' if self.pk else 'create')),
                       kwargs={'pk': self.pk} if self.pk else None)


class AlwaysUpdateFieldsMixin(object):
    """
    Ensure fields listed in the attribute ``self.always_update_fields`` are always updated by ``self.save()``.
    Makes the usage of ``self.save(update_fields=...)`` cleaner.
    """

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        if update_fields:
            update_fields = set(update_fields)
            update_fields.update(self.always_update_fields)
            kwargs['update_fields'] = update_fields
        return super(AlwaysUpdateFieldsMixin, self).save(*args, **kwargs)


class AutoUpdateFieldsMixin(object):
    """
    Keep track of what fields were set in order to make UPDATE queries lighter.

    This mix-in comes with the following features:
    * Foreign keys and the mutable types are correctly handled.
    * Models with a primary key preset to a value before being saved in database are correctly handled.
    * The return value of the overloaded methods is not swallowed but returned.

    However this low-memory footprint mix-in also comes with some limitations, it does not:
    * Store old fields values - you cannot know if the fields are really modified or not.
    * Watch for background modifications of the mutable fields - it can drives you crazy, sometimes.
    * Detect fields with `auto_*_now=True` - you have to set `auto_fields` to those fields names.

    Set `default_force_update` to True to raise a :class:`DatabaseError` if the UPDATE did not affect any rows. The
    default avoids this exception but the instance is not protected from saving all rows in database instead of 0!
    """

    auto_fields = ()
    default_force_update = False

    def __init__(self, *args, **kwargs):
        super(AutoUpdateFieldsMixin, self).__init__(*args, **kwargs)
        self.setted_fields = set()

    def __setattr__(self, name, value):
        try:
            # Check the instance is both initialized and already stored in DB
            if hasattr(self, 'setted_fields') and not self._state.adding:
                field, model, direct, m2m = self._meta.get_field_by_name(name)
                # Check some properties of the field
                if direct and not m2m and not field.primary_key:
                    self.setted_fields.add(name)
        except FieldDoesNotExist:  # The attribute is not a field
            pass
        return super(AutoUpdateFieldsMixin, self).__setattr__(name, value)

    def get_auto_fields(self):
        return self.auto_fields

    def save(self, *args, **kwargs):
        if not self._state.adding and hasattr(self, 'fields_in_db') and not kwargs.get('force_insert'):
            kwargs.setdefault('force_update', self.default_force_update)
            kwargs.setdefault('update_fields', set(itertools.chain(self.setted_fields, self.get_auto_fields())))
        returned = super(AutoUpdateFieldsMixin, self).save(*args, **kwargs)
        self.setted_fields = set()
        return returned


class MapUniqueTogetherMixin(object):

    map_exclude_fields = ()

    def _perform_unique_checks(self, unique_checks):
        errors = super(MapUniqueTogetherMixin, self)._perform_unique_checks(unique_checks)
        non_field_errors = errors.pop(NON_FIELD_ERRORS, [])
        for error in non_field_errors:
            for field in error.params['unique_check']:
                if field not in self.map_exclude_fields:
                    errors.setdefault(field, []).append(self.unique_error_message(error.params['model_class'], [field]))
        return errors


class MapUniqueTogetherIntegrityErrorToValidationErrorMixin(object):

    @property
    def unique_together_set(self):
        return [set(fields) for fields in self._meta.unique_together]

    def save(self, *args, **kwargs):
        try:
            return super(MapUniqueTogetherIntegrityErrorToValidationErrorMixin, self).save(*args, **kwargs)
        except IntegrityError as e:
            match = re.search(r'duplicate key[^\)]+\((?P<fields>[^\)]+)\)', e.args[0])
            if match:
                fields = set(f.strip().replace('_id', '') for f in match.groupdict()['fields'].split(','))
                if fields in self.unique_together_set:
                    raise self.unique_error_message(self.__class__, fields)
            raise


class ReloadMixin(object):

    def reload(self):
        return self.__class__.objects.get(pk=self.pk)


class SaveInstanceFilesMixin(object):
    """
    Overrides saves() with a method that saves the instance first and then the instance's file fields this ensure
    that the upload_path method will get a valid instance id / private key.
    """
    def save(self, *args, **kwargs):
        saved_fields = {}
        if self.pk is None:
            for field in self._meta.fields:
                if isinstance(field, FileField):
                    saved_fields[field.name] = getattr(self, field.name)
                    setattr(self, field.name, None)
            super(SaveInstanceFilesMixin, self).save(*args, **kwargs)
            for name, value in saved_fields.iteritems():
                setattr(self, name, value)
            kwargs['force_insert'] = False  # Do not force insert because we already saved the instance
        super(SaveInstanceFilesMixin, self).save(*args, **kwargs)


class UpdatePreconditionsMixin(object):

    def apply_preconditions(self, base_qs, using, pk_val, values, update_fields, force_update):
        if self._pre_excludes:
            base_qs = base_qs.exclude(**self._pre_excludes)
        if self._pre_filters:
            base_qs = base_qs.filter(**self._pre_filters)
        return base_qs, using, pk_val, values, update_fields, force_update

    def pop_preconditions(self, *args, **kwargs):
        self._pre_excludes = kwargs.pop('pre_excludes', {})
        self._pre_filters = kwargs.pop('pre_filters', {})
        return args, kwargs

    def save(self, *args, **kwargs):
        args, kwargs = self.pop_preconditions(*args, **kwargs)
        try:
            return super(UpdatePreconditionsMixin, self).save(*args, **kwargs)
        except DatabaseError as e:
            if 'update_fields did not affect' in '{0}'.format(e):
                raise exceptions.DatabaseUpdatePreconditionsError()
            raise

    def _do_update(self, base_qs, using, pk_val, values, update_fields, force_update):
        update = super(UpdatePreconditionsMixin, self)._do_update
        return update(*self.apply_preconditions(base_qs, using, pk_val, values, update_fields, force_update))


class ValidateOnSaveMixin(object):

    def save(self, *args, **kwargs):
        # FIXME throws a ValidationError if using get_or_create() to instantiate model!
        #if not kwargs.get('force_insert', False):
        if kwargs.pop('validate', True):
            self.full_clean()
        super(ValidateOnSaveMixin, self).save(*args, **kwargs)
