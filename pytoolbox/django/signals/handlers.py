# -*- encoding: utf-8 -*-

"""
    :file:`apps.py` ::

        from django import apps
        from django.utils.translation import ugettext_lazy as _

        from . import signals

        __all__ = ('MyApp', )


        class MyAppConfig(apps.AppConfig):
            name = 'myapp'
            verbose_name = _('My Application')

            def ready(self):
                signals.connect(self)

    :file:`signals.py` ::

        from django.db.models import signals as dj_signals
        from django.db.backends import signals as dj_db_signals
        from pytoolbox.django.signals import (
            create_site, setup_postgresql_hstore_extension, strip_strings_and_validate_model
        )

        # ...

        def connect(config):
            '''Connect signal handlers to signals.'''
            dj_db_signals.connection_created.connect(setup_postgresql_hstore_extension)
            dj_signals.post_migrate.connect(create_site, sender=config)
            dj_signals.pre_save.connect(
                strip_strings_and_validate_model, sender=settings.AUTH_USER_MODEL)
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import logging

from django.conf import settings
from django.db.models import fields
from django.db.models.fields.files import FileField

from pytoolbox import module
from pytoolbox.encoding import PY2, string_types

_all = module.All(globals())

logger = logging.getLogger(__name__)


def clean_files_delete_handler(instance, signal, **kwargs):
    """
    Remove the files of the instance's file fields when it is removed from the database.

    Simply use ``post_delete.connect(clean_files_delete_handler, sender=<your_model_class>)``

    .. warning::
        This function remove the file without worrying about any other instance using this file !

    .. note::
        Project `django-cleanup <https://github.com/un1t/django-cleanup>`_
        is a more complete alternative.
    """
    for field in kwargs['sender']._meta.fields:
        if isinstance(field, FileField):
            file_field = getattr(instance, field.name)
            if file_field.path:
                file_field.delete(save=False)


def create_site(sender, **kwargs):
    """
    Ensure the site name and domain is well configured.

    Some alternative:

    * Loading an initial fixture with the values for the site
    * The application `django-defaultsite <https://github.com/oppian/django-defaultsite>`_
    * Other options discussed `here <https://groups.google.com/forum/#!topic/django-developers/X-ef0C0V8Rk>`_
    """
    from django.contrib.sites import models as site_app
    site_fields = {'domain': settings.SITE_DOMAIN, 'name': settings.SITE_NAME}
    site = site_app.Site.objects.update_or_create(pk=settings.SITE_ID, defaults=site_fields)[0]
    logger.info(
        'Updated settings of Site "{0.name}" with ID {0.pk} and domain {0.domain}'.format(site))


def setup_postgresql_hstore_extension(sender, connection, **kwargs):
    from psycopg2.extras import register_hstore
    cursor = connection.connection.cursor()
    cursor.execute('CREATE EXTENSION IF NOT EXISTS hstore')
    if PY2:
        register_hstore(connection.connection, globally=True, unicode=True)
    else:
        register_hstore(connection.connection, globally=True)


def strip_strings_and_validate_model(sender, instance, raw, **kwargs):
    """Strip the string fields of the instance and run the instance's full_clean()."""
    if not raw:
        logger.debug('Validate model {0} on save() with kwargs={1}'.format(instance, kwargs))
        for field in instance._meta.fields:
            if isinstance(field, (fields.CharField, fields.TextField)):
                field_value = getattr(instance, field.name)
                if isinstance(field_value, string_types):
                    setattr(instance, field.name, field_value.strip())
        instance.full_clean()


__all__ = _all.diff(globals())
