# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2015 David Fischer. All rights reserved.
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

import itertools

from django.db import DatabaseError
from django.utils.translation import ugettext_lazy as _

from ... import exceptions, module

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
    errors.extend(itertools.chain.from_iterable(v for v in getattr(validation_error, 'error_dict', {}).values()))
    return any(e.code == code for e in errors)


def iter_errors_info(validation_error):
    """
    **Example usage**

    >>> from django.core.exceptions import ValidationError
    >>> from pytoolbox.unittest import asserts
    >>> eq = lambda i, l: asserts.list_equal(list(i), l)
    >>> eq(iter_errors_info(ValidationError('yo', code='bad')), [(None, 'yo', 'bad')])
    >>> eq(iter_errors_info(ValidationError({'__all__': ValidationError('yo', code='x')})), [('__all__', 'yo', 'x')])
    >>> eq(iter_errors_info(ValidationError([ValidationError('yo')])), [(None, 'yo', None)])
    """
    if hasattr(validation_error, 'error_dict'):
        for field, errors in validation_error.error_dict.items():
            for error in errors:
                yield field, get_message(error), error.code
    else:
        for error in validation_error.error_list:
            yield None, get_message(error), error.code


class DatabaseUpdatePreconditionsError(exceptions.MessageMixin, DatabaseError):
    message = _('Row update request preconditions failed: A concurrent request changed the row in database.')


class InvalidStateError(exceptions.MessageMixin, Exception):
    message = _('State of {instance} is {instance.state}, excepted in any of {states}.')


class TransitionNotAllowedError(exceptions.MessageMixin, Exception):
    message = _('Cannot change state of {instance} from {instance.state} to {state}.')

__all__ = _all.diff(globals())
