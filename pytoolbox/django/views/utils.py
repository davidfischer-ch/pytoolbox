# -*- encoding: utf-8 -*-

"""
Some utilities related to the view layer.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from django.http import Http404

from pytoolbox import module

_all = module.All(globals())


def get_model_or_404(name, *models):
    try:
        return next(m for m in models if m._meta.model_name == name)
    except StopIteration:
        raise Http404()


__all__ = _all.diff(globals())
