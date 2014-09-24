# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                                        PYTOOLBOX - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2014 David Fischer. All rights reserved.
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

import os, requests, urllib2, urlparse
from codecs import open

from ..encoding import to_bytes
from ..exception import BadHTTPResponseCodeError, CorruptedFileError

__all__ = ('download', 'download_ext', 'get_request_data')


def download(url, filename):
    """Read the content of given ``url`` and save it as a file ``filename``."""
    with open(filename, 'wb') as f:
        f.write(urllib2.urlopen(url).read())


def download_ext(url, filename, code=200, chunk_size=102400, force=True, hash_method=None, expected_hash=None,
                 progress_callback=None, code_msg='Download request {url} code {r_code} expected {code}.',
                 hash_msg='Downloaded file {filename} is corrupted.',  **kwargs):
    """
    Read the content of given ``url`` and save it as a file ``filename``, extended version.

    * Set ``code`` to expected response code.
    * Set ``force`` to False to avoid downloading the file if it already exists.
    * Set ``hash_method`` to any callable with this signature: ``file_hash = (filename, is_filename=True)``.
    * Set ``expected_hash`` to the expected hash value, warning: this will force computing the hash of the file.
    * Set ``kwargs`` to any extra argument accepted by ``requests.get()``.

    **Example usage**

    >>> from nose.tools import assert_raises as ar_
    >>> from pytoolbox.crypto import githash
    >>> url = 'http://techslides.com/demos/sample-videos/small.mp4'

    >>> download_ext(url, 'small.mp4')
    (True, True, None)
    >>> download_ext(url, 'small.mp4', force=False)
    (True, False, None)
    >>> download_ext(url, 'small.mp4', force=False, hash_method=githash)
    (True, False, '1fc478842f51e7519866f474a02ad605235bc6a6')

    >>> download_ext(url, 'small.mp4', hash_method=githash, expected_hash='1fc478842f51e7519866f474a02ad605235bc6a6')
    (True, True, '1fc478842f51e7519866f474a02ad605235bc6a6')

    >>> def progress(current, total):
    ...     print('(%d, %d)' % (current, total))

    >>> download_ext(url, 'small.mp4', progress_callback=progress)
    (102400, 383631)
    (204800, 383631)
    (307200, 383631)
    (383631, 383631)
    (True, True, None)

    >>> ar_(CorruptedFileError, download_ext, url, 'small.mp4', hash_method=githash,
    ...     expected_hash='2ad605235bc6a6842f51e7519866f1fc478474a0')

    >>> download_ext('http://techslides.com/monkey.mp4', 'monkey.mp4', code=404)
    (False, False, None)

    >>> ar_(BadHTTPResponseCodeError, download_ext, 'http://techslides.com/monkey.mp4', 'monkey.mp4')
    """
    exists, downloaded = os.path.exists(filename), False
    if force or not exists:
        response = requests.get(url, stream=bool(chunk_size), **kwargs)
        length = response.headers.get('content-length')
        if response.status_code != code:
            raise BadHTTPResponseCodeError(code_msg.format(url=url, code=code, r_code=response.status_code))
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                if chunk_size:
                    # chunked download (may report progress as a progress bar)
                    position, length = 0, None if length is None else int(length)
                    for data in response.iter_content(chunk_size):
                        f.write(data)
                        if progress_callback:
                            position += len(data)
                            progress_callback(position, length)
                else:
                    f.write(response.content)
            downloaded = True
    file_hash = hash_method(filename, is_filename=True) if hash_method else None
    if expected_hash and file_hash != expected_hash:
        raise CorruptedFileError(hash_msg.format(filename=filename, file_hash=file_hash, expected_hash=expected_hash))
    return exists, downloaded, file_hash


def get_request_data(request, accepted_keys=None, required_keys=None, sources=['query', 'form', 'json'],
                     qs_only_first_value=False, optional=False):
    """
    Return a python dictionary containing the values retrieved from various attributes (sources) of the request.

    This function is specifically implemented to retrieve data from an instance of ``werkzeug.wrappers.Request`` or
    ``django.http.request.HttpRequest`` by only using ``getattr`` to respect the duck typing philosophy.

    FIXME : Add an example that have a JSON content ....

    **Example usage**

    >>> from cStringIO import StringIO
    >>> from nose.tools import eq_
    >>> from werkzeug.wrappers import Request

    >>> d = 'key1=this+is+encoded+form+data&key2=another'
    >>> q = 'foo=bar&blah=blafasel'
    >>> c = 'application/x-www-form-urlencoded'
    >>> r = Request.from_values(query_string=q, content_length=len(d), input_stream=StringIO(d), content_type=c)

    >>> all = {'blah': ['blafasel'], 'foo': ['bar'], 'key1': ['this is encoded form data'], 'key2': ['another']}
    >>> eq_(get_request_data(r), all)

    Restrict valid keys:

    >>> get_request_data(r, accepted_keys=['foo']) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: Invalid key "..." from the request, valid: [...'foo'].

    Requires specific keys:

    >>> get_request_data(r, required_keys=['foo', 'THE_key']) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: Missing key "THE_key from the request, required: [...'foo', ...'THE_key'].

    Retrieve data with or without a fallback to an empty string (JSON content):

    >>> get_request_data(r, sources=['json'], optional=True)
    {}
    >>> get_request_data(r, sources=['json'])
    Traceback (most recent call last):
        ...
    ValueError: Unable to retrieve any data from the request.

    The order of the sources is important:

    >>> d = 'foo=bar+form+data'
    >>> q = 'foo=bar+query+string&it=works'
    >>> r = Request.from_values(query_string=q, content_length=len(d), input_stream=StringIO(d), content_type=c)
    >>> eq_(get_request_data(r, sources=['query', 'form']), {'it': ['works'], 'foo': ['bar form data']})
    >>> eq_(get_request_data(r, sources=['form', 'query']), {'it': ['works'], 'foo': ['bar query string']})

    Retrieve only the first value of the keys (Query string):

    >>> r = Request.from_values(query_string='foo=bar+1&foo=bar+2&foo=bar+3', content_type=c)
    >>> eq_(get_request_data(r, sources=['query']), {'foo': ['bar 1', 'bar 2', 'bar 3']})
    >>> eq_(get_request_data(r, sources=['query'], qs_only_first_value=True), {'foo': 'bar 1'})

    """
    data = {}
    for source in sources:
        if source == 'form':
            data.update(getattr(request, 'form', {}))  # werkzeug
        elif source == 'json':
            data.update(getattr(request, 'get_json', lambda: {})() or {})  # werkzeug
        elif source == 'query':
            query_dict = getattr(request, 'args',  # werkzeug
                                 urlparse.parse_qs(getattr(request, 'META', {}).get('QUERY_STRING', '')))  # django
            if qs_only_first_value:
                for key, value in query_dict.iteritems():
                    data[key] = value[0] if isinstance(value, list) else value
            else:
                data.update(query_dict)

    if required_keys is not None:
        for key in required_keys:
            if not key in data:
                raise ValueError(to_bytes('Missing key "{0} from the request, required: {1}.'.format(
                                 key, required_keys)))
    if accepted_keys is not None:
        for key in data:
            if not key in accepted_keys:
                raise ValueError(to_bytes('Invalid key "{0}" from the request, valid: {1}.'.format(
                                 key, accepted_keys)))
    if not data and not optional:
        raise ValueError(to_bytes('Unable to retrieve any data from the request.'))
    return data or {}
