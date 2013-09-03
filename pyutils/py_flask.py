# -*- coding: utf-8 -*-

#**************************************************************************************************#
#                               PYUTILS - SOME PYTHON UTILITY FUNCTIONS
#
#   Description : Toolbox for Python scripts
#   Authors     : David Fischer
#   Contact     : david.fischer.ch@gmail.com
#   Copyright   : 2013-2013 David Fischer. All rights reserved.
#**************************************************************************************************#
#
#  This file is part of pyutils.
#
#  This project is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with this project.
#  If not, see <http://www.gnu.org/licenses/>
#
#  Retrieved from git clone https://github.com/davidfischer-ch/pyutils.git

from bson.objectid import ObjectId
from flask import abort, Response
from werkzeug.exceptions import HTTPException
from py_serialization import object2json
from py_validation import valid_uuid

STATUS_TO_EXCEPTION = {400: TypeError, 404: IndexError, 415: ValueError, 501: NotImplementedError}


def check_id(id):
    if valid_uuid(id, objectid_allowed=False, none_allowed=False):
        return id
    elif valid_uuid(id, objectid_allowed=True, none_allowed=False):
        return ObjectId(id)
    raise ValueError(u'Wrong id format {0}'.format(id))


def get_request_data(request, required_keys=[], fail=True):
    data = request.get_json(silent=True)
    if data is None:
        data = {}
        for x in request.form:
            data[x] = request.form.get(x)
    for key in required_keys:
        if not key in data:
            raise ValueError(u'Missing key "{0}" from JSON content.'.format(key))
    if not data and fail:
        raise ValueError(u'Requires JSON content or form-data.')
    return data or {}


def map_exceptions(e):
    u"""
    Maps a standard exception into corresponding HTTP exception class.

    **Example usage**:

    >>> map_exceptions(TypeError())
    Traceback (most recent call last):
        ...
    ClientDisconnected: 400: Bad Request

    >>> map_exceptions(IndexError())
    Traceback (most recent call last):
        ...
    NotFound: 404: Not Found

    >>> map_exceptions(NotImplementedError())
    Traceback (most recent call last):
        ...
    NotImplemented: 501: Not Implemented

    Any instance of HTTPException is simply raised without any mapping:

    >>> map_exceptions(HTTPException())
    Traceback (most recent call last):
        ...
    NotImplemented: 501: Not Implemented

    Convert a JSON response of kind {'status': 200, 'value': '...'}:

    >>> map_exceptions({'status': 200, 'value': 'The good value.'})
    'The good value.'
    >>> map_exceptions({'status': 415, 'value': 'The value is bad.'})
    Traceback (most recent call last):
        ...
    ValueError: The value is bad.
    """
    if isinstance(e, dict):
        if e['status'] == 200:
            return e['value']
        exception = STATUS_TO_EXCEPTION.get(e['status'], Exception)
        raise exception(e['value'])
    elif isinstance(e, HTTPException):
        raise
    elif isinstance(e, TypeError):
        abort(400, unicode(e))
    elif isinstance(e, KeyError):
        abort(400, u'Key {0} not found.'.format(e))
    elif isinstance(e, IndexError):
        abort(404, unicode(e))
    elif isinstance(e, ValueError):
        abort(415, unicode(e))
    elif isinstance(e, NotImplementedError):
        abort(501, unicode(e))
    else:
        abort(500, '{0} {1} {2}'.format(e.__class__.__name__, repr(e), unicode(e)))


def json_response(status, value=None, include_properties=False):
    response = Response(
        response=object2json({u'status': status, u'value': value}, include_properties),
        status=status, mimetype=u'application/json')
    response.status_code = status
    return response
