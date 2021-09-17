import functools, os, sys, time, urllib.request, urllib.error, urllib.parse

import requests

from pytoolbox import console, crypto, filesystem, module
from pytoolbox.exceptions import BadHTTPResponseCodeError, CorruptedFileError

_all = module.All(globals())


def download(url, path):
    """Read the content of given `url` and save it as a file `path`."""
    with open(path, 'wb') as target:
        with urllib.request.urlopen(url) as source:
            target.write(source.read())


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


def iter_download_to_file(
    url,
    path,
    code=200,
    chunk_size=102400,
    force=True,
    hash_algorithm=None,
    expected_hash=None,
    **kwargs
):
    position = length = 0
    chunk = file_hash = None
    downloaded = False
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
                file = file or open(path, 'wb')  # pylint: disable=consider-using-with
                file.write(chunk)
        finally:
            if file:
                file.close()
        if file_hash:
            file_hash = file_hash.hexdigest()

    elif hash_algorithm:
        file_hash = crypto.checksum(
            path,
            is_path=True,
            algorithm=hash_algorithm,
            chunk_size=chunk_size)

    if expected_hash and file_hash != expected_hash:
        raise CorruptedFileError(path=path, file_hash=file_hash, expected_hash=expected_hash)

    if not downloaded:
        yield position, length, chunk, downloaded, file_hash


def download_ext(  # pylint:disable=too-many-locals
    url,
    path,
    code=200,
    chunk_size=102400,
    force=True,
    hash_algorithm=None,
    expected_hash=None,
    progress_callback=None,
    **kwargs
):
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
    >>> from pytoolbox import filesystem
    >>> from pytoolbox.unittest import asserts
    >>>
    >>> _ = filesystem.remove('small.mp4')
    >>>
    >>> url = 'https://pytoolbox.s3-eu-west-1.amazonaws.com/tests/small.mp4'
    >>>
    >>> download_ext(url, 'small.mp4')
    (False, True, None)
    >>> download_ext(url, 'small.mp4', force=False)
    (True, False, None)
    >>>
    >>> download_ext(url, 'small.mp4', force=False, hash_algorithm='md5',
    ...              expected_hash='a3ac7ddabb263c2d00b73e8177d15c8d')
    (True, False, 'a3ac7ddabb263c2d00b73e8177d15c8d')
    >>>
    >>> def progress(start_time, position, length, chunk):
    ...     print('(%d, %d)' % (position, length))
    >>>
    >>> download_ext(url, 'small.mp4', progress_callback=progress)
    (102400, 383631)
    (204800, 383631)
    (307200, 383631)
    (383631, 383631)
    (True, True, None)
    >>>
    >>> with asserts.raises(CorruptedFileError):
    ...     download_ext(
    ...         url,
    ...         'small.mp4',
    ...         hash_algorithm=hashlib.md5,
    ...         expected_hash='efac5df252145c2d07b73e8177d15c8d')
    >>>
    >>> download_ext('http://techslides.com/monkey.mp4', 'monkey.mp4', code=404)
    (False, False, None)
    >>>
    >>> with asserts.raises(BadHTTPResponseCodeError):
    ...     download_ext('http://techslides.com/monkey.mp4', 'monkey.mp4')
    """
    downloaded = False
    exists = os.path.exists(path)
    file_hash = None
    start_time = time.time()
    for position, length, chunk, downloaded, file_hash in iter_download_to_file(
        url, path, code, chunk_size, force, hash_algorithm, expected_hash, **kwargs
    ):
        if progress_callback:
            progress_callback(start_time, position, length, chunk)
    return exists, downloaded, file_hash


def download_ext_multi(
    resources,
    chunk_size=1024 * 1024,
    progress_callback=console.progress_bar,
    progress_stream=sys.stdout,
    progress_template='\r[{counter} of {total}] [{done}{todo}] {name}'
):
    """
    Download resources, showing a progress bar by default.

    Each element should be a `dict` with the url, path and name keys.
    Any extra item is passed to :func:`iter_download_to_file` as extra keyword arguments.
    """
    for counter, resource in enumerate(sorted(resources, key=lambda r: r['name']), 1):
        kwargs = resource.copy()
        start_time = time.time()
        url = kwargs.pop('url')
        path = kwargs.pop('path')
        name = kwargs.pop('name')

        callback = functools.partial(
            progress_callback,
            stream=progress_stream,
            template=progress_template.format(
                counter=counter,
                done='{done}',
                name=name,
                todo='{todo}',
                total=len(resources)))

        if not os.path.exists(path):
            filesystem.makedirs(os.path.dirname(path))
            try:
                for returned in iter_download_to_file(
                    url, path, chunk_size=chunk_size, force=False, **kwargs
                ):
                    callback(start_time, returned[0], returned[1])
            except Exception:
                filesystem.remove(path)
                raise

        callback(start_time, 1, 1)
        progress_stream.write(os.linesep)


__all__ = _all.diff(globals())
