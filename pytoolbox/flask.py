# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import logging, uuid

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
        return uuid.UUID(id)
    elif ObjectId is not None and valid_uuid(id, objectid_allowed=True, none_allowed=False):
        return ObjectId(id)
    raise ValueError('Wrong id format {0}'.format(id))


def map_exceptions(exception):
    """
    Maps a standard `exception` into corresponding HTTP exception class.

    **Example usage**

    >>> from werkzeug import exceptions as w_exceptions
    >>> from pytoolbox.unittest import asserts
    >>> asserts.raises(w_exceptions.BadRequest, map_exceptions, TypeError('test'))
    >>> asserts.raises(w_exceptions.NotFound, map_exceptions, IndexError('test'))
    >>> asserts.raises(w_exceptions.NotImplemented, map_exceptions, NotImplementedError('test'))

    Any instance of HTTPException is simply raised without any mapping:

    >>> asserts.raises(w_exceptions.ImATeapot, map_exceptions, w_exceptions.ImATeapot('test'))
    >>> asserts.raises(w_exceptions.NotFound, map_exceptions, w_exceptions.NotFound('test'))

    Convert a JSON response of kind {'status': 200, 'value': '...'}:

    >>> print(map_exceptions({'status': 200, 'value': 'The good value.'}))
    The good value.
    >>> map_exceptions({'status': 415, 'value': 'The value is bad.'})
    Traceback (most recent call last):
        ...
    ValueError: The value is bad.
    """
    if isinstance(exception, Exception):
        try:
            logging.exception(exception)
        except AttributeError:
            logging.exception(repr(exception))
    if isinstance(exception, dict):
        if exception['status'] == 200:
            return exception['value']
        exception_class = STATUS_TO_EXCEPTION.get(exception['status'], Exception)
        raise exception_class(exception['value'])
    elif isinstance(exception, HTTPException):
        raise exception
    elif isinstance(exception, TypeError):
        abort(400, text_type(exception))
    elif isinstance(exception, KeyError):
        abort(400, 'Key {0} not found.'.format(exception))
    elif isinstance(exception, IndexError):
        abort(404, text_type(exception))
    elif isinstance(exception, ValueError):
        abort(415, text_type(exception))
    elif isinstance(exception, NotImplementedError):
        abort(501, text_type(exception))
    else:
        abort(500, '{0} {1} {2}'.format(
            exception.__class__.__name__, repr(exception), text_type(exception)))


def json_response(status, value=None, include_properties=False):
    response = Response(
        response=object_to_json({'status': status, 'value': value}, include_properties),
        status=status, mimetype='application/json')
    response.status_code = status
    return response


__all__ = _all.diff(globals())
