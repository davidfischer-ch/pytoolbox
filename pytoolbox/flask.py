# -*- encoding: utf-8 -*-

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
