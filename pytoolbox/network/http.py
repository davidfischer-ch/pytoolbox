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

import hashlib, os, requests, time, urllib2, urlparse
from codecs import open

from ..crypto import checksum
from ..encoding import to_bytes
from ..filesystem import get_bytes
from ..exception import BadHTTPResponseCodeError, CorruptedFileError

__all__ = ('download', 'download_ext', 'get_request_data')


def download(url, filename):
    """Read the content of given ``url`` and save it as a file ``filename``."""
    with open(filename, 'wb') as f:
        f.write(urllib2.urlopen(url).read())


def download_ext(url, filename, code=200, chunk_size=102400, force=True, hash_method=None, hash_algorithm=None,
                 expected_hash=None, progress_callback=None, **kwargs):
    """
    Read the content of given `url` and save it as a file `filename`, extended version.

    * Set `code` to expected response code.
    * Set `force` to False to avoid downloading the file if it already exists.
    * Set `hash_method` to a callable with the signature ``hash_method(filename, is_filename=True, chunk_size=102400)``.
    * Set `hash_algorithm` to a string or a method from the :mod:`hashlib`.
    * Set `expected_hash` to the expected hash value, warning: this will force computing the hash of the file.
    * Set `kwargs` to any extra argument accepted by ``requests.get()``.

    If `chunk_size` and `hash_algorithm` are both set then the hash algorithm will be called for every chunk of data,
    this may optimize the performances. In any case, if a hash method or algorithm is defined then you will get a hash
    even if the file is already downloaded.

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

    >>> download_ext(url, 'small.mp4', force=False, hash_algorithm='md5',
    ...              expected_hash='a3ac7ddabb263c2d00b73e8177d15c8d')
    (True, False, 'a3ac7ddabb263c2d00b73e8177d15c8d')

    >>> def progress(start_time, current, total):
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
    if hash_method is not None and hash_algorithm is not None:
        raise ValueError('You can set hash_method or hash_algorithm, not both.')
    exists, downloaded = os.path.exists(filename), False
    file_hash = None
    if force or not exists:
        response = requests.get(url, stream=bool(chunk_size), **kwargs)
        length = response.headers.get('content-length')
        if response.status_code != code:
            raise BadHTTPResponseCodeError(url=url, code=code, r_code=response.status_code)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                if chunk_size:
                    # May compute hash on chunks
                    if hash_algorithm is not None:
                        file_hash = hashlib.new(hash_algorithm)
                    start_time = time.time()
                    # chunked download (may report progress as a progress bar)
                    position, length = 0, None if length is None else int(length)
                    for data in response.iter_content(chunk_size):
                        if file_hash:
                            file_hash.update(get_bytes(data))
                        f.write(data)
                        if progress_callback is not None:
                            position += len(data)
                            progress_callback(start_time, position, length)
                else:
                    f.write(response.content)
            downloaded = True
    if file_hash:  # was computed during the download
        file_hash = file_hash.hexdigest()
    else:  # is not yet computed for any valid reason
        if hash_method is not None:
            file_hash = hash_method(filename, is_filename=True, chunk_size=chunk_size)
        elif hash_algorithm is not None:
            file_hash = checksum(filename, is_filename=True, algorithm=hash_algorithm, chunk_size=chunk_size)
    if expected_hash is not None and file_hash != expected_hash:
        raise CorruptedFileError(filename=filename, file_hash=file_hash, expected_hash=expected_hash)
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
            if key not in data:
                raise ValueError(to_bytes('Missing key "{0} from the request, required: {1}.'.format(
                                 key, required_keys)))
    if accepted_keys is not None:
        for key in data:
            if key not in accepted_keys:
                raise ValueError(to_bytes('Invalid key "{0}" from the request, valid: {1}.'.format(
                                 key, accepted_keys)))
    if not data and not optional:
        raise ValueError(to_bytes('Unable to retrieve any data from the request.'))
    return data or {}
