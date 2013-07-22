#!/usr/bin/env python
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
from pyutils import object2json, valid_uuid


def check_id(id):
    if valid_uuid(id, objectid_allowed=False, none_allowed=False):
        return id
    elif valid_uuid(id, objectid_allowed=True, none_allowed=False):
        return ObjectId(id)
    raise ValueError('Wrong id format %s' % id)


def get_request_json(request, required_keys=[]):
    try:
        data = request.json
    except:
        raise ValueError('Requires valid JSON content-type.')
    for key in required_keys:
        if not key in data:
            raise ValueError('Missing key "%s" from JSON content.' % key)
    if not data:
        raise ValueError('Requires JSON content-type.')
    return data


def map_exceptions(e):
    if isinstance(e, HTTPException):
        raise
    if isinstance(e, TypeError):
        abort(400, str(e))
    elif isinstance(e, KeyError):
        abort(400, 'Key %s not found.' % e)
    elif isinstance(e, IndexError):
        abort(404, str(e))
    elif isinstance(e, ValueError):
        abort(415, str(e))
    elif isinstance(e, NotImplementedError):
        abort(501, str(e))
    abort(500, '%s %s %s' % (e.__class__.__name__, repr(e), str(e)))


def json_response(status, value=None):
    response = Response(response=object2json({'status': status, 'value': value}, False),
                        status=status, mimetype="application/json")
    response.status_code = status
    return response
