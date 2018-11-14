# -*- encoding: utf-8 -*-

"""
Extra fields for your forms.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import copy

from django import forms

from pytoolbox import module

_all = module.All(globals())


class StripCharField(forms.RegexField):
    default_widget_attrs = {'autofocus': 'autofocus'}
    max_length = None

    def __init__(self, **kwargs):
        attrs = copy.deepcopy(self.default_widget_attrs)
        attrs.update(kwargs.pop('widget_attrs', None) or {})
        super(StripCharField, self).__init__(
            r'\S+', max_length=self.max_length, widget=forms.TextInput(attrs), **kwargs)


__all__ = _all.diff(globals())
