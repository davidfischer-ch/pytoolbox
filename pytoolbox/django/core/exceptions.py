# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import itertools

from django.db import DatabaseError
from django.utils.translation import ugettext_lazy as _

from pytoolbox import exceptions, module

_all = module.All(globals())


def get_message(validation_error):
    message, params = validation_error.message, validation_error.params
    return message % params if params else message


def has_code(validation_error, code):
    """
    **Example usage**

    >>> from django.core.exceptions import ValidationError
    >>> has_code(ValidationError('yo'), 'bad')
    False
    >>> has_code(ValidationError('yo', code='bad'), 'bad')
    True
    >>> has_code(ValidationError({'__all__': ValidationError('yo')}), 'bad')
    False
    >>> has_code(ValidationError({'__all__': ValidationError('yo', code='bad')}), 'bad')
    True
    >>> has_code(ValidationError([ValidationError('yo')]), 'bad')
    False
    >>> has_code(ValidationError([ValidationError('yo', code='bad')]), 'bad')
    True
    """
    errors = getattr(validation_error, 'error_list', [])
    errors.extend(itertools.chain.from_iterable(
        v for v in getattr(validation_error, 'error_dict', {}).itervalues()))
    return any(e.code == code for e in errors)


def iter_validation_errors(validation_error):
    """
    **Example usage**

    >>> from django.core.exceptions import ValidationError
    >>> from pytoolbox.unittest import asserts
    >>> eq = lambda i, l: asserts.list_equal(list(i), l)
    >>> bad, boy = ValidationError('yo', code='bad'), ValidationError('yo', code='boy')
    >>> eq(iter_validation_errors(bad), [(None, bad)])
    >>> eq(iter_validation_errors(ValidationError({'__all__': boy})), [('__all__', boy)])
    >>> eq(iter_validation_errors(ValidationError([bad, boy])), [(None, bad), (None, boy)])
    """
    if hasattr(validation_error, 'error_dict'):
        for field, errors in validation_error.error_dict.iteritems():
            for error in errors:
                yield field, error
    else:
        for error in validation_error.error_list:
            yield None, error


class DatabaseUpdatePreconditionsError(exceptions.MessageMixin, DatabaseError):
    message = _('Row update request preconditions failed: '
                'A concurrent request changed the row in database.')


class InvalidStateError(exceptions.MessageMixin, Exception):
    message = _('State of {instance} is {instance.state}, excepted in any of {states}.')


class TransitionNotAllowedError(exceptions.MessageMixin, Exception):
    message = _('Cannot change state of {instance} from {instance.state} to {state}.')


__all__ = _all.diff(globals())
