# -*- encoding: utf-8 -*-

"""
Decorators for enhancing your models.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from django.core.urlresolvers import reverse

from pytoolbox import module

_all = module.All(globals())


def with_urls(base_url, *interface_actions, **kwargs):
    base_url = base_url + ':'
    if not interface_actions:
        raise ValueError('At least one action should be defined')
    singleton = kwargs.pop('singleton', False)
    if kwargs:
        raise AttributeError(kwargs)

    def _with_urls(model):
        model.interface_actions = interface_actions
        for action in interface_actions:
            method_name = 'get_{0}_url'.format(action)
            if hasattr(model, method_name):
                continue
            if action == 'create':
                @classmethod
                def method(cls):
                    return reverse(base_url + 'create')
            else:
                def get_url(action, singleton):
                    if singleton:
                        def _get_url(self):
                            return reverse(base_url + action)
                    else:
                        def _get_url(self):
                            return reverse(base_url + action, args=[str(self.pk)])
                    return _get_url
                method = get_url(action, singleton)
            method.__name__ = method_name
            setattr(model, method_name, method)
        if 'detail' in interface_actions:
            # Add get_absolute_url for Django to be happy
            model.get_absolute_url = model.get_detail_url
        return model
    return _with_urls


__all__ = _all.diff(globals())
