# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
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

import urllib2, urlparse
from codecs import open
from ..encoding import to_bytes


def download(url, filename):
    u"""Read the content of given ``url`` and save it as a file ``filename``."""
    with open(filename, u'wb') as f:
        f.write(urllib2.urlopen(url).read())


def get_request_data(request, accepted_keys=None, required_keys=None, sources=[u'query', u'form', u'json'],
                     qs_only_first_value=False, optional=False):
    u"""
    Return a python dictionary containing the values retrieved from various attributes (sources) of the request.

    This function is specifically implemented to retrieve data from an instance of ``werkzeug.wrappers.Request`` or
    ``django.http.request.HttpRequest`` by only using ``getattr`` to respect the duck typing philosophy.

    FIXME : Add an example that have a JSON content ....

    **Example usage**

    >>> from cStringIO import StringIO
    >>> from nose.tools import eq_
    >>> from werkzeug.wrappers import Request

    >>> d = u'key1=this+is+encoded+form+data&key2=another'
    >>> q = u'foo=bar&blah=blafasel'
    >>> c = u'application/x-www-form-urlencoded'
    >>> r = Request.from_values(query_string=q, content_length=len(d), input_stream=StringIO(d), content_type=c)

    >>> all = {'blah': ['blafasel'], 'foo': ['bar'], 'key1': [u'this is encoded form data'], 'key2': [u'another']}
    >>> eq_(get_request_data(r), all)

    Restrict valid keys:

    >>> get_request_data(r, accepted_keys=[u'foo']) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: Invalid key "..." from the request, valid: [...'foo'].

    Requires specific keys:

    >>> get_request_data(r, required_keys=[u'foo', u'THE_key']) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: Missing key "THE_key from the request, required: [...'foo', ...'THE_key'].

    Retrieve data with or without a fallback to an empty string (JSON content):

    >>> get_request_data(r, sources=[u'json'], optional=True)
    {}
    >>> get_request_data(r, sources=[u'json'])
    Traceback (most recent call last):
        ...
    ValueError: Unable to retrieve any data from the request.

    The order of the sources is important:

    >>> d = u'foo=bar+form+data'
    >>> q = u'foo=bar+query+string&it=works'
    >>> r = Request.from_values(query_string=q, content_length=len(d), input_stream=StringIO(d), content_type=c)
    >>> eq_(get_request_data(r, sources=[u'query', u'form']), {'it': ['works'], 'foo': [u'bar form data']})
    >>> eq_(get_request_data(r, sources=[u'form', u'query']), {'it': ['works'], 'foo': [u'bar query string']})

    Retrieve only the first value of the keys (Query string):

    >>> r = Request.from_values(query_string=u'foo=bar+1&foo=bar+2&foo=bar+3', content_type=c)
    >>> eq_(get_request_data(r, sources=[u'query']), {u'foo': [u'bar 1', u'bar 2', u'bar 3']})
    >>> eq_(get_request_data(r, sources=[u'query'], qs_only_first_value=True), {'foo': 'bar 1'})

    """
    data = {}
    for source in sources:
        if source == u'form':
            data.update(getattr(request, u'form', {}))  # werkzeug
        elif source == u'json':
            data.update(getattr(request, u'get_json', lambda: {})() or {})  # werkzeug
        elif source == u'query':
            query_dict = getattr(request, u'args',  # werkzeug
                                 urlparse.parse_qs(getattr(request, u'META', {}).get(u'QUERY_STRING', u'')))  # django
            if qs_only_first_value:
                for key, value in query_dict.iteritems():
                    data[key] = value[0] if isinstance(value, list) else value
            else:
                data.update(query_dict)

    if required_keys is not None:
        for key in required_keys:
            if not key in data:
                raise ValueError(to_bytes(u'Missing key "{0} from the request, required: {1}.'.format(
                                 key, required_keys)))
    if accepted_keys is not None:
        for key in data:
            if not key in accepted_keys:
                raise ValueError(to_bytes(u'Invalid key "{0}" from the request, valid: {1}.'.format(
                                 key, accepted_keys)))
    if not data and not optional:
        raise ValueError(to_bytes(u'Unable to retrieve any data from the request.'))
    return data or {}
