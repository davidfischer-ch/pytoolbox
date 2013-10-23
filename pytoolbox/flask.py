# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                       PYUTILS - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
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

import logging, urlparse, warnings
from bson.objectid import ObjectId
from flask import abort, Response
from werkzeug.exceptions import HTTPException
from .encoding import to_bytes
from .serialization import object2dictV2, object2json
from .validation import valid_uuid

STATUS_TO_EXCEPTION = {400: TypeError, 404: IndexError, 415: ValueError, 501: NotImplementedError}


def check_id(id):
    if valid_uuid(id, objectid_allowed=False, none_allowed=False):
        return id
    elif valid_uuid(id, objectid_allowed=True, none_allowed=False):
        return ObjectId(id)
    raise ValueError(u'Wrong id format {0}'.format(id))


def get_request_data(request, accepted_keys=None, required_keys=None, query_string=True, qs_only_first_value=False,
                     fail=True):

    warnings.warn(to_bytes(u'Please use the new implementation from the module pytoolbox.network.http'),
                  DeprecationWarning, stacklevel=2)

    data = request.get_json(silent=True)
    source = u'form-data' if data is None else u'JSON content'
    if data is None:
        if query_string:
            data = urlparse.parse_qs(request.query_string)
            if qs_only_first_value:
                data = {key: value[0] if isinstance(value, list) else value for key, value in data.iteritems()}
        else:
            data = {}
        for key in request.form:
            data[key] = request.form.get(key)
    if required_keys is not None:
        for key in required_keys:
            if not key in data:
                raise ValueError(to_bytes(u'Missing key "{0}" from {1}, required: {2}.'.format(
                                 key, source, required_keys)))
    if accepted_keys is not None:
        for key in data:
            if not key in accepted_keys:
                raise ValueError(to_bytes(u'Invalid key "{0}" from {1}, valid: {2}.'.format(
                                 key, source, accepted_keys)))
    if not data and fail:
        raise ValueError(to_bytes(u'Requires JSON content or form-data.'))
    return data or {}


def map_exceptions(e):
    u"""
    Maps a standard exception into corresponding HTTP exception class.

    **Example usage**

    >>> from nose.tools import assert_raises
    >>> import werkzeug.exceptions
    >>> assert_raises(werkzeug.exceptions.BadRequest, map_exceptions, TypeError('test'))
    >>> assert_raises(werkzeug.exceptions.NotFound, map_exceptions, IndexError(u'test'))
    >>> assert_raises(werkzeug.exceptions.NotImplemented, map_exceptions, NotImplementedError(u'test'))

    Any instance of HTTPException is simply raised without any mapping:

    >>> assert_raises(werkzeug.exceptions.ImATeapot, map_exceptions, werkzeug.exceptions.ImATeapot(u'test'))
    >>> assert_raises(werkzeug.exceptions.NotFound, map_exceptions, werkzeug.exceptions.NotFound(u'test'))

    Convert a JSON response of kind {'status': 200, 'value': '...'}:

    >>> map_exceptions({'status': 200, 'value': 'The good value.'})
    u'The good value.'
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


def json_response2dict(response, remove_underscore):
    value = []
    if response[u'status'] == 200:
        try:
            for thing in response[u'value']:
                value.append(object2dictV2(thing, remove_underscore=remove_underscore))
        except TypeError:
            value.append(object2dictV2(response[u'value'], remove_underscore=remove_underscore))
    return value
