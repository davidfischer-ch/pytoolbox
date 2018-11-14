# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import functools, os, sys, time, urllib2, urlparse
from codecs import open  # pylint:disable=redefined-builtin

import requests

from pytoolbox import console, crypto, module
from pytoolbox.encoding import to_bytes
from pytoolbox.exceptions import BadHTTPResponseCodeError, CorruptedFileError
from pytoolbox.filesystem import makedirs, remove

_all = module.All(globals())


def download(url, path):
    """Read the content of given `url` and save it as a file `path`."""
    with open(path, 'wb') as f:
        f.write(urllib2.urlopen(url).read())


def iter_download_core(url, code=200, chunk_size=102400, **kwargs):
    response = requests.get(url, stream=bool(chunk_size), **kwargs)
    length = response.headers.get('content-length')
    if response.status_code != code:
        raise BadHTTPResponseCodeError(url=url, code=code, r_code=response.status_code)
    if response.status_code == 200:
        if chunk_size:
            position, length = 0, None if length is None else int(length)
            for chunk in response.iter_content(chunk_size):
                position += len(chunk)
                yield position, length, chunk
        else:
            chunk = response.content
            yield len(chunk), len(chunk), chunk


def iter_download_to_file(url, path, code=200, chunk_size=102400, force=True, hash_algorithm=None,
                          expected_hash=None, **kwargs):
    position, length, chunk, downloaded, file_hash = 0, 0, None, False, None
    if force or not os.path.exists(path):
        file = None
        try:
            for position, length, chunk in iter_download_core(url, code, chunk_size, **kwargs):
                downloaded = True
                if hash_algorithm:
                    file_hash = file_hash or crypto.new(hash_algorithm)
                    file_hash.update(chunk)
                file_hash_digest = file_hash.hexdigest() if file_hash else None
                yield position, length, chunk, downloaded, file_hash_digest
                file = file or open(path, 'wb')
                file.write(chunk)
        finally:
            if file:
                file.close()
        if file_hash:
            file_hash = file_hash.hexdigest()
    elif hash_algorithm:
        file_hash = crypto.checksum(
            path, is_path=True, algorithm=hash_algorithm, chunk_size=chunk_size)
    if expected_hash and file_hash != expected_hash:
        raise CorruptedFileError(path=path, file_hash=file_hash, expected_hash=expected_hash)
    if not downloaded:
        yield position, length, chunk, downloaded, file_hash


def download_ext(url, path, code=200, chunk_size=102400, force=True, hash_algorithm=None,
                 expected_hash=None, progress_callback=None, **kwargs):
    """
    Read the content of given `url` and save it as a file `path`, extended version.

    * Set `code` to expected response code.
    * Set `force` to False to avoid downloading the file if it already exists.
    * Set `hash_algorithm` to a string or a method from the :mod:`hashlib`.
    * Set `expected_hash` to the expected hash value, warning: this will force computing the hash of
      the file.
    * Set `kwargs` to any extra argument accepted by ``requests.get()``.

    If `chunk_size` and `hash_algorithm` are both set then the hash algorithm will be called for
    every chunk of data, this may optimize the performances. In any case, if a hash algorithm is
    defined then you will get a hash even if the file is already downloaded.

    **Example usage**

    >>> import hashlib
    >>> from pytoolbox.unittest import asserts
    >>> url = 'http://techslides.com/demos/sample-videos/small.mp4'

    >>> download_ext(url, 'small.mp4')
    (True, True, None)
    >>> download_ext(url, 'small.mp4', force=False)
    (True, False, None)

    >>> download_ext(url, 'small.mp4', force=False, hash_algorithm='md5',
    ...              expected_hash='a3ac7ddabb263c2d00b73e8177d15c8d')
    (True, False, 'a3ac7ddabb263c2d00b73e8177d15c8d')

    >>> def progress(start_time, position, length, chunk):
    ...     print('(%d, %d)' % (position, length))

    >>> download_ext(url, 'small.mp4', progress_callback=progress)
    (102400, 383631)
    (204800, 383631)
    (307200, 383631)
    (383631, 383631)
    (True, True, None)

    >>> asserts.raises(
    ...     CorruptedFileError,
    ...     download_ext, url, 'small.mp4', hash_algorithm=hashlib.md5,
    ...     expected_hash='efac5df252145c2d07b73e8177d15c8d')

    >>> download_ext('http://techslides.com/monkey.mp4', 'monkey.mp4', code=404)
    (False, False, None)

    >>> asserts.raises(
    ...     BadHTTPResponseCodeError,
    ...     download_ext, 'http://techslides.com/monkey.mp4', 'monkey.mp4')
    """
    exists, start_time = os.path.exists(path), time.time()
    for position, length, chunk, downloaded, file_hash in iter_download_to_file(
        url, path, code, chunk_size, force, hash_algorithm, expected_hash, **kwargs
    ):
        if progress_callback:
            progress_callback(start_time, position, length, chunk)
    return exists, downloaded, file_hash


def download_ext_multi(resources, chunk_size=1024 * 1024, progress_callback=console.progress_bar,
                       progress_stream=sys.stdout,
                       progress_template='\r[{counter} of {total}] [{done}{todo}] {name}'):
    """
    Download resources, showing a progress bar by default.

    Each element should be a `dict` with the url, path and name keys.
    Any extra item is passed to :func:`iter_download_to_file` as extra keyword arguments.
    """
    for counter, resource in enumerate(sorted(resources, key=lambda r: r['name']), 1):
        kwargs, start_time = resource.copy(), time.time()
        url, path, name = kwargs.pop('url'), kwargs.pop('path'), kwargs.pop('name')
        callback = functools.partial(
            progress_callback,
            stream=progress_stream,
            template=progress_template.format(
                counter=counter, done='{done}', name=name, todo='{todo}', total=len(resources)))
        if not os.path.exists(path):
            makedirs(os.path.dirname(path))
            try:
                for returned in iter_download_to_file(
                    url, path, chunk_size=chunk_size, force=False, **kwargs
                ):
                    callback(start_time, returned[0], returned[1])
            except:
                remove(path)
                raise
        callback(start_time, 1, 1)
        progress_stream.write(os.linesep)


def get_request_data(request, accepted_keys=None, required_keys=None,
                     sources=('query', 'form', 'json'), qs_only_first_value=False, optional=False):
    """
    Return a python dictionary containing the values retrieved from various attributes (sources) of
    the request.

    This function is specifically implemented to retrieve data from an instance of
    `werkzeug.wrappers.Request` or `django.http.request.HttpRequest` by only using `getattr` to
    respect the duck typing philosophy.

    FIXME : Add an example that have a JSON content ....

    **Example usage**

    >>> from cStringIO import StringIO
    >>> from pytoolbox.unittest import asserts
    >>> from werkzeug.wrappers import Request

    >>> d = 'key1=this+is+encoded+form+data&key2=another'
    >>> q = 'foo=bar&blah=blafasel'
    >>> c = 'application/x-www-form-urlencoded'
    >>> r = Request.from_values(
    ...         query_string=q, content_length=len(d), input_stream=StringIO(d), content_type=c)

    >>> asserts.dict_equal(get_request_data(r), {
    ...     'blah': ['blafasel'],
    ...     'foo': ['bar'],
    ...     'key1': ['this is encoded form data'],
    ...     'key2': ['another']
    ... })

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
    >>> r = Request.from_values(
    ...         query_string=q, content_length=len(d), input_stream=StringIO(d), content_type=c)
    >>> asserts.dict_equal(get_request_data(r, sources=['query', 'form']), {
    ...     'it': ['works'], 'foo': ['bar form data']
    ... })
    >>> asserts.dict_equal(get_request_data(r, sources=['form', 'query']), {
    ...     'it': ['works'], 'foo': ['bar query string']
    ... })

    Retrieve only the first value of the keys (Query string):

    >>> r = Request.from_values(query_string='foo=bar+1&foo=bar+2&foo=bar+3', content_type=c)
    >>> asserts.dict_equal(get_request_data(r, sources=['query']), {
    ...     'foo': ['bar 1', 'bar 2', 'bar 3']
    ... })
    >>> asserts.dict_equal(get_request_data(r, sources=['query'], qs_only_first_value=True), {
    ...     'foo': 'bar 1'
    ... })

    """
    data = {}
    for source in sources:
        if source == 'form':
            data.update(getattr(request, 'form', {}))  # werkzeug
        elif source == 'json':
            data.update(getattr(request, 'get_json', lambda: {})() or {})  # werkzeug
        elif source == 'query':
            query_dict = getattr(
                request, 'args',  # werkzeug
                urlparse.parse_qs(getattr(request, 'META', {}).get('QUERY_STRING', '')))  # django
            if qs_only_first_value:
                for key, value in query_dict.iteritems():
                    data[key] = value[0] if isinstance(value, list) else value
            else:
                data.update(query_dict)

    if required_keys is not None:
        for key in required_keys:
            if key not in data:
                raise ValueError(to_bytes(
                    'Missing key "{0} from the request, required: {1}.'.format(key, required_keys)))
    if accepted_keys is not None:
        for key in data:
            if key not in accepted_keys:
                raise ValueError(to_bytes('Invalid key "{0}" from the request, valid: {1}.'.format(
                                 key, accepted_keys)))
    if not data and not optional:
        raise ValueError(to_bytes('Unable to retrieve any data from the request.'))
    return data or {}


__all__ = _all.diff(globals())
