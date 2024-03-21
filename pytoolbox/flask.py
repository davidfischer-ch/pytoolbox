from __future__ import annotations

import logging
import uuid

from flask import abort, Response
from werkzeug.exceptions import HTTPException

from .private import ObjectId
from .serialization import object_to_json
from .validation import valid_uuid

__all__ = ['STATUS_TO_EXCEPTION', 'check_id', 'json_response', 'map_exceptions']

STATUS_TO_EXCEPTION = {400: TypeError, 404: IndexError, 415: ValueError, 501: NotImplementedError}


def check_id(value):
    if valid_uuid(value, objectid_allowed=False, none_allowed=False):
        return uuid.UUID(value)
    if ObjectId is not None and valid_uuid(value, objectid_allowed=True, none_allowed=False):
        return ObjectId(value)
    raise ValueError(f'Wrong id format {value}')


def json_response(status, value=None, include_properties=False):
    response = Response(
        response=object_to_json({'status': status, 'value': value}, include_properties),
        status=status,
        mimetype='application/json')
    response.status_code = status
    return response


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
    if isinstance(exception, HTTPException):
        raise exception
    if isinstance(exception, TypeError):
        abort(400, str(exception))
    elif isinstance(exception, KeyError):
        abort(400, f'Key {exception} not found.')
    elif isinstance(exception, IndexError):
        abort(404, str(exception))
    elif isinstance(exception, ValueError):
        abort(415, str(exception))
    elif isinstance(exception, NotImplementedError):
        abort(501, str(exception))
    else:
        abort(500, f'{exception.__class__.__name__} {repr(exception)} {str(exception)}')
    return None
