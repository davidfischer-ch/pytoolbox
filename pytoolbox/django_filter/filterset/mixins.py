# -*- encoding: utf-8 -*-

"""
Mix-ins for building your own `Django Filter <https://github.com/alex/django-filter>`_
powered filters.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from pytoolbox import module

_all = module.All(globals())


class RaiseOnUnhandledFieldClassMixin(object):
    """
    Raise an exception when the filter set is unable to find a suitable filter for any of the model
    fields to filter.
    """

    @classmethod
    def filter_for_field(cls, f, name, lookup_type='exact'):
        value = super(RaiseOnUnhandledFieldClassMixin, cls).filter_for_field(f, name, lookup_type)
        if not value:
            raise NotImplementedError(
                "Unable to find a suitable filter for field '{1}' of class {0.__class__} "
                "with lookup type '{2}'".format(f, name, lookup_type))
        return value


__all__ = _all.diff(globals())
