"""Tests for the network.http module."""

# pylint: disable=use-implicit-booleaness-not-comparison

from __future__ import annotations

import hashlib
import io
import threading
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator
from http.client import HTTPResponse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import override
from unittest import mock

import pytest
import requests

from pytoolbox.exceptions import CorruptedFileError
from pytoolbox.network import http

type Origin = Callable[[int, dict[str, str], bytes], str]


@pytest.fixture(name='origin')
def fixture_origin() -> Iterator[Origin]:
    """
    Yield a function setting the response of a local HTTP server, and returning a URL it serves.
    """
    responses: list[tuple[int, dict[str, str], bytes]] = []

    class Handler(BaseHTTPRequestHandler):
        """Request handler sending the last response set to every GET."""

        def do_GET(self) -> None:  # pylint: disable=invalid-name
            """Send the last response set."""
            status, headers, body = responses[-1]
            self.send_response(status)
            for name, value in headers.items():
                self.send_header(name, value)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        @override
        def log_message(self, format: str, *args: object) -> None:
            pass

    def set_response(status: int, headers: dict[str, str], body: bytes) -> str:
        responses.append((status, headers, body))
        return f'http://127.0.0.1:{server.server_address[1]}/file.bin'

    with ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        yield set_response
        server.shutdown()
        thread.join()


def test_download_keeps_the_existing_file_when_the_request_fails(
    tmp_path: Path,
    origin: Origin,
) -> None:
    """A failed request leaves the file it would have replaced untouched."""
    path = tmp_path / 'file.bin'
    path.write_bytes(b'good')

    with pytest.raises(urllib.error.HTTPError) as error:
        http.download(origin(500, {}, b'error'), path)
    error.value.close()

    assert path.read_bytes() == b'good'
    assert list(tmp_path.iterdir()) == [path]


def test_download_refuses_a_redirect_to_another_scheme(tmp_path: Path, origin: Origin) -> None:
    """A redirect cannot take the download to a scheme the URL itself is refused for."""
    path = tmp_path / 'file.bin'
    url = origin(302, {'Location': 'ftp://127.0.0.1:1/file.bin'}, b'')

    with (
        mock.patch.object(
            urllib.request.FTPHandler,
            'ftp_open',
            side_effect=AssertionError('FTP opened'),
        ) as ftp_open,
        pytest.raises(ValueError),
    ):
        http.download(url, path)

    ftp_open.assert_not_called()
    assert list(tmp_path.iterdir()) == []


def test_download_refusal_quotes_no_credential_of_the_address(
    tmp_path: Path,
    origin: Origin,
) -> None:
    """A refused redirect's error holds neither the credentials nor the query of its address."""
    url = origin(302, {'Location': 'ftp://user:secret@host/x?key=k'}, b'')

    with pytest.raises(ValueError) as error:
        http.download(url, tmp_path / 'file.bin')

    assert 'secret' not in str(error.value)
    assert 'key=k' not in str(error.value)


def test_download_reads_the_body_in_bounded_chunks(tmp_path: Path, origin: Origin) -> None:
    """The body is copied a chunk at a time, never buffered whole in memory."""
    path = tmp_path / 'file.bin'
    body = b'x' * (http.DEFAULT_CHUNK_SIZE * 2 + 1)

    with mock.patch.object(
        HTTPResponse,
        'read',
        autospec=True,
        side_effect=HTTPResponse.read,
    ) as read:
        http.download(origin(200, {}, body), path)

    assert path.read_bytes() == body
    read_sizes = [call.args[1] if len(call.args) > 1 else None for call in read.call_args_list]
    assert None not in read_sizes


def test_download_ext_keeps_the_existing_file_when_the_body_fails_its_checksum(
    tmp_path: Path,
) -> None:
    """A body failing its checksum never replaces the file, nor lingers beside it."""
    path = tmp_path / 'file.bin'
    path.write_bytes(b'good')

    with (
        mock.patch.object(requests, 'get', return_value=_response(b'evil')),
        pytest.raises(CorruptedFileError),
    ):
        http.download_ext(
            'http://example.com/file.bin',
            path,
            hash_algorithm='sha256',
            expected_hash=hashlib.sha256(b'other').hexdigest(),
        )

    assert path.read_bytes() == b'good'
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize('error', [requests.ConnectionError(), KeyboardInterrupt()])
def test_download_ext_leaves_no_file_when_the_transfer_breaks(
    tmp_path: Path,
    error: BaseException,
) -> None:
    """A transfer broken after its first chunk, or interrupted, leaves no partial file behind."""
    path = tmp_path / 'file.bin'

    with (
        mock.patch.object(requests, 'get', return_value=_response(b'part', error)),
        pytest.raises(type(error)),
    ):
        http.download_ext('http://example.com/file.bin', path)

    assert list(tmp_path.iterdir()) == []


def test_download_ext_multi_checks_the_hash_of_an_existing_file(tmp_path: Path) -> None:
    """A file already at the path is accepted only if it matches the hash pinned for it."""
    path = tmp_path / 'file.bin'
    path.write_bytes(b'truncated')
    resource = http.Resource(
        name='file',
        url='http://example.com/file.bin',
        path=path,
        hash_algorithm='sha256',
        expected_hash=hashlib.sha256(b'body').hexdigest(),
    )

    with (
        mock.patch.object(requests, 'get', return_value=_response(b'body')),
        pytest.raises(CorruptedFileError),
    ):
        http.download_ext_multi([resource], progress_stream=io.StringIO())


def test_download_ext_multi_downloads_an_existing_file_again_when_forced(tmp_path: Path) -> None:
    """Forcing replaces the file already at the path with the downloaded body."""
    path = tmp_path / 'file.bin'
    path.write_bytes(b'old')
    resource = http.Resource(name='file', url='http://example.com/file.bin', path=path)

    with mock.patch.object(requests, 'get', return_value=_response(b'new')):
        http.download_ext_multi([resource], force=True, progress_stream=io.StringIO())

    assert path.read_bytes() == b'new'


def test_download_ext_multi_leaves_no_file_when_interrupted(tmp_path: Path) -> None:
    """An interrupted download leaves nothing a later run would take for complete."""
    path = tmp_path / 'file.bin'
    resource = http.Resource(name='file', url='http://example.com/file.bin', path=path)

    with (
        mock.patch.object(requests, 'get', return_value=_response(b'part', KeyboardInterrupt())),
        pytest.raises(KeyboardInterrupt),
    ):
        http.download_ext_multi([resource], progress_stream=io.StringIO())

    assert list(tmp_path.iterdir()) == []


# --- Internals ------------------------------------------------------------------------------------


def _response(*chunks: bytes | BaseException) -> mock.Mock:
    """Return a 200 response streaming *chunks*, raising an exception met among them."""

    def iter_content(chunk_size: int) -> Iterator[bytes]:  # pylint: disable=unused-argument
        for chunk in chunks:
            if isinstance(chunk, BaseException):
                raise chunk
            yield chunk

    return mock.Mock(status_code=200, headers={}, iter_content=iter_content)
