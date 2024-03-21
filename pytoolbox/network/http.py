from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, Protocol, TextIO
import functools
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import requests
from requests.auth import AuthBase

from pytoolbox import console, crypto, filesystem, module
from pytoolbox.exceptions import BadHTTPResponseCodeError, CorruptedFileError

_all = module.All(globals())

DEFAULT_CHUNK_SIZE: Final[int] = 100 * 1024


@dataclass(frozen=True, slots=True)
class Resource(object):  # pylint:disable=too-many-instance-attributes
    name: str
    url: str
    path: Path

    hash_algorithm: Callable | str | None = None
    expected_hash: str | None = None

    allow_redirects: bool = True
    auth: AuthBase | tuple[str, str] | None = None
    cert: str | tuple[str, str] | None = None
    cookies: dict[str, str] | None = None
    headers: dict[str, str] | None = None
    params: dict | list[tuple] | bytes | None = None
    proxies: dict[str, str] | None = None
    timeout: int | None = None
    verify: bool = True


class SingleProgressCallback(Protocol):  # pylint:disable=too-few-public-methods
    def __call__(self, start_time: float, position: int, length: int, chunk: bytes | None) -> None:
        ...


class MultiProgressCallback(Protocol):  # pylint:disable=too-few-public-methods
    def __call__(
        self,
        *,
        start_time: float,
        current: int,
        total: int,
        stream: TextIO,
        template: str
    ) -> None:
        ...


def download(url: str, path: Path) -> None:
    """Read the content of given `url` and save it as a file `path`."""
    with path.open('wb') as target:
        with urllib.request.urlopen(url) as source:
            target.write(source.read())


# TODO Unpacking Resource for declaring parameters in a DRY manner
# I would like to make code DRY, such as unpacking Resource to define function's arguments
# However its not possible as of today, see https://github.com/python/typing/issues/1495

def iter_download_core(  # pylint:disable=too-many-arguments
    url: str,
    *,
    code: int = 200,
    chunk_size: int | None = DEFAULT_CHUNK_SIZE,

    allow_redirects: bool = True,
    auth: AuthBase | tuple[str, str] | None = None,
    cert: str | tuple[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    params: dict | list[tuple] | bytes | None = None,
    proxies: dict[str, str] | None = None,
    timeout: int | None = None,
    verify: bool = True
) -> Iterator[tuple[int, int, bytes]]:
    response = requests.get(
        url=url,
        allow_redirects=allow_redirects,
        auth=auth,
        cert=cert,
        cookies=cookies,
        headers=headers,
        params=params,
        proxies=proxies,
        stream=bool(chunk_size),
        timeout=timeout,
        verify=verify
    )
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


def iter_download_to_file(  # pylint:disable=too-many-arguments,too-many-locals
    url: str,
    path: Path,
    *,
    code: int = 200,
    chunk_size: int | None = DEFAULT_CHUNK_SIZE,
    force: bool = True,
    hash_algorithm: Callable | str | None = None,
    expected_hash: str | None = None,

    allow_redirects: bool = True,
    auth: AuthBase | tuple[str, str] | None = None,
    cert: str | tuple[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    params: dict | list[tuple] | bytes | None = None,
    proxies: dict[str, str] | None = None,
    timeout: int | None = None,
    verify: bool = True
) -> Iterator[tuple[int, int, bytes | None, bool, str | None]]:
    position = length = 0
    chunk: bytes | None = None
    file_hasher = None
    file_hash: str | None = None
    downloaded: bool = False
    if force or not path.exists():
        file = None
        try:
            for position, length, chunk in iter_download_core(
                url=url,
                code=code,
                chunk_size=chunk_size,
                allow_redirects=allow_redirects,
                auth=auth,
                cert=cert,
                cookies=cookies,
                headers=headers,
                params=params,
                proxies=proxies,
                timeout=timeout,
                verify=verify
            ):
                downloaded = True
                if hash_algorithm:
                    if file_hasher is None:
                        file_hasher = crypto.new(hash_algorithm)
                    file_hasher.update(chunk)  # type: ignore[attr-defined]
                    file_hash = file_hasher.hexdigest()  # type: ignore[attr-defined]
                yield position, length, chunk, downloaded, file_hash
                file = file or path.open('wb')  # pylint: disable=consider-using-with
                file.write(chunk)
        finally:
            if file:
                file.close()
    elif hash_algorithm:
        file_hash = crypto.checksum(path, algorithm=hash_algorithm, chunk_size=chunk_size)

    if expected_hash and file_hash != expected_hash:
        raise CorruptedFileError(path=path, file_hash=file_hash, expected_hash=expected_hash)

    if not downloaded:
        yield position, length, chunk, downloaded, file_hash


def download_ext(  # pylint:disable=too-many-arguments,too-many-locals
    url: str,
    path: Path,
    *,
    code: int = 200,
    chunk_size: int | None = DEFAULT_CHUNK_SIZE,
    force: bool = True,

    hash_algorithm: Callable | str | None = None,
    expected_hash: str | None = None,
    progress_callback: SingleProgressCallback | None = None,

    allow_redirects: bool = True,
    auth: AuthBase | tuple[str, str] | None = None,
    cert: str | tuple[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    params: dict | list[tuple] | bytes | None = None,
    proxies: dict[str, str] | None = None,
    timeout: int | None = None,
    verify: bool = True
) -> tuple[bool, bool, str | None]:
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
    >>> from pathlib import Path
    >>>
    >>> from pytoolbox import filesystem
    >>> from pytoolbox.unittest import asserts
    >>>
    >>> _ = filesystem.remove('small.mp4')
    >>>
    >>> base_url = 'https://pytoolbox.s3-eu-west-1.amazonaws.com'
    >>>
    >>> download_ext(f'{base_url}/tests/small.mp4', Path('small.mp4'))
    (False, True, None)
    >>> download_ext(f'{base_url}/tests/small.mp4', Path('small.mp4'), force=False)
    (True, False, None)
    >>>
    >>> download_ext(
    ...     f'{base_url}/tests/small.mp4',
    ...     Path('small.mp4'),
    ...     force=False,
    ...     hash_algorithm='md5',
    ...     expected_hash='a3ac7ddabb263c2d00b73e8177d15c8d')
    (True, False, 'a3ac7ddabb263c2d00b73e8177d15c8d')
    >>>
    >>> def progress(start_time, position, length, chunk):
    ...     print('(%d, %d)' % (position, length))
    >>>
    >>> download_ext(f'{base_url}/tests/small.mp4', Path('small.mp4'), progress_callback=progress)
    (102400, 383631)
    (204800, 383631)
    (307200, 383631)
    (383631, 383631)
    (True, True, None)
    >>>
    >>> with asserts.raises(CorruptedFileError):
    ...     download_ext(
    ...         f'{base_url}/tests/small.mp4',
    ...         Path('small.mp4'),
    ...         hash_algorithm=hashlib.md5,
    ...         expected_hash='efac5df252145c2d07b73e8177d15c8d')
    >>>
    >>> download_ext(f'{base_url}/missing', Path('missing'), code=404)
    (False, False, None)
    >>>
    >>> with asserts.raises(BadHTTPResponseCodeError):
    ...     download_ext(f'{base_url}/missing', Path('missing'))
    """
    downloaded: bool = False
    exists: bool = path.exists()
    file_hash: str | None = None
    start_time = time.time()
    for position, length, chunk, downloaded, file_hash in iter_download_to_file(
        url=url,
        path=path,
        code=code,
        chunk_size=chunk_size,
        force=force,
        hash_algorithm=hash_algorithm,
        expected_hash=expected_hash,
        allow_redirects=allow_redirects,
        auth=auth,
        cert=cert,
        cookies=cookies,
        headers=headers,
        params=params,
        proxies=proxies,
        timeout=timeout,
        verify=verify
    ):
        if progress_callback:
            progress_callback(start_time=start_time, position=position, length=length, chunk=chunk)
    return exists, downloaded, file_hash


def download_ext_multi(
    resources: Iterable[Resource],
    *,
    code: int = 200,
    chunk_size: int | None = 1024 * 1024,
    force: bool = False,
    progress_callback: MultiProgressCallback = console.progress_bar,
    progress_stream=sys.stdout,
    progress_template='\r[{counter} of {total}] [{done}{todo}] {resource.name}'
):
    """
    Download resources, showing a progress bar by default.

    Create any required directories recursively.

    Each element should be a `dict` with the url, path and name keys.
    Any extra item is passed to :func:`iter_download_to_file` as extra keyword arguments.
    """
    resources = list(resources)  # Allow to pass an iterable and consome it once
    for counter, resource in enumerate(resources, 1):
        callback = functools.partial(
            progress_callback,
            start_time=time.time(),
            stream=progress_stream,
            template=progress_template.format(
                resource=resource,
                counter=counter,
                done='{done}',
                todo='{todo}',
                total=len(resources)))

        if not resource.path.exists():
            filesystem.makedirs(resource.path, parent=True)
            try:
                for returned in iter_download_to_file(
                    code=code,
                    chunk_size=chunk_size,
                    force=force,
                    **asdict(resource)
                ):
                    callback(current=returned[0], total=returned[1])
            except Exception:
                filesystem.remove(resource.path)
                raise

        callback(current=1, total=1)
        progress_stream.write(os.linesep)


__all__ = _all.diff(globals())
