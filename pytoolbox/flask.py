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

import logging

from flask import abort, Response
from werkzeug.exceptions import HTTPException

from . import module
from .encoding import text_type
from .private import ObjectId
from .serialization import object_to_json
from .validation import valid_uuid

_all = module.All(globals())

STATUS_TO_EXCEPTION = {400: TypeError, 404: IndexError, 415: ValueError, 501: NotImplementedError}


def check_id(id):
    if valid_uuid(id, objectid_allowed=False, none_allowed=False):
        return id
    elif valid_uuid(id, objectid_allowed=True, none_allowed=False):
        return ObjectId(id)
    raise ValueError('Wrong id format {0}'.format(id))


def map_exceptions(e):
    """
    Maps a standard exception into corresponding HTTP exception class.

    **Example usage**

    >>> from nose.tools import assert_raises
    >>> import werkzeug.exceptions
    >>> assert_raises(werkzeug.exceptions.BadRequest, map_exceptions, TypeError('test'))
    >>> assert_raises(werkzeug.exceptions.NotFound, map_exceptions, IndexError('test'))
    >>> assert_raises(werkzeug.exceptions.NotImplemented, map_exceptions, NotImplementedError('test'))

    Any instance of HTTPException is simply raised without any mapping:

    >>> assert_raises(werkzeug.exceptions.ImATeapot, map_exceptions, werkzeug.exceptions.ImATeapot('test'))
    >>> assert_raises(werkzeug.exceptions.NotFound, map_exceptions, werkzeug.exceptions.NotFound('test'))

    Convert a JSON response of kind {'status': 200, 'value': '...'}:

    >>> print(map_exceptions({'status': 200, 'value': 'The good value.'}))
    The good value.
    >>> map_exceptions({'status': 415, 'value': 'The value is bad.'})
    Traceback (most recent call last):
        ...
    ValueError: The value is bad.
    """
    if isinstance(e, Exception):
        try:
            logging.exception(e)
        except AttributeError:
            logging.exception(repr(e))
    if isinstance(e, dict):
        if e['status'] == 200:
            return e['value']
        exception = STATUS_TO_EXCEPTION.get(e['status'], Exception)
        raise exception(e['value'])
    elif isinstance(e, HTTPException):
        raise e
    elif isinstance(e, TypeError):
        abort(400, text_type(e))
    elif isinstance(e, KeyError):
        abort(400, 'Key {0} not found.'.format(e))
    elif isinstance(e, IndexError):
        abort(404, text_type(e))
    elif isinstance(e, ValueError):
        abort(415, text_type(e))
    elif isinstance(e, NotImplementedError):
        abort(501, text_type(e))
    else:
        abort(500, '{0} {1} {2}'.format(e.__class__.__name__, repr(e), text_type(e)))


def json_response(status, value=None, include_properties=False):
    response = Response(
        response=object_to_json({'status': status, 'value': value}, include_properties),
        status=status, mimetype='application/json')
    response.status_code = status
    return response

__all__ = _all.diff(globals())
