"""
Extra fields for your forms.
"""
from __future__ import annotations

import copy

from django import forms

__all__ = ['StripCharField']


class StripCharField(forms.RegexField):
    default_widget_attrs = {'autofocus': 'autofocus'}
    max_length = None

    def __init__(self, **kwargs):
        attrs = copy.deepcopy(self.default_widget_attrs)
        attrs.update(kwargs.pop('widget_attrs', None) or {})
        super().__init__(
            r'\S+',
            max_length=self.max_length,
            widget=forms.TextInput(attrs),
            **kwargs)
