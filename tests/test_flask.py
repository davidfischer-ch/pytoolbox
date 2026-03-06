from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from werkzeug import exceptions as w_exceptions

from pytoolbox import flask as flask_utils


# check_id() tests -------------------------------------------------------


def test_check_id_valid_uuid() -> None:
    """check_id() returns a UUID object for a valid UUID string."""
    value = str(uuid.uuid4())
    result = flask_utils.check_id(value)
    assert isinstance(result, uuid.UUID)
    assert str(result) == value


def test_check_id_invalid() -> None:
    """check_id() raises ValueError for an invalid id format."""
    with pytest.raises(ValueError, match='Wrong id format'):
        flask_utils.check_id('not-a-valid-id')


def test_check_id_objectid_when_bson_available() -> None:
    """check_id() returns an ObjectId when bson is available."""
    mock_objectid_cls = MagicMock()
    mock_objectid_instance = MagicMock()
    mock_objectid_cls.return_value = mock_objectid_instance
    value = '507f1f77bcf86cd799439011'
    with (
        patch.object(flask_utils, 'ObjectId', mock_objectid_cls),
        patch.object(flask_utils, 'valid_uuid') as mock_valid
    ):
        mock_valid.side_effect = lambda v, **kw: (
            kw.get('objectid_allowed', False)
        )
        result = flask_utils.check_id(value)
    assert result is mock_objectid_instance


# map_exceptions() tests -------------------------------------------------


def test_map_exceptions_type_error() -> None:
    """map_exceptions() aborts with 400 for TypeError."""
    with pytest.raises(w_exceptions.BadRequest):
        flask_utils.map_exceptions(TypeError('bad type'))


def test_map_exceptions_key_error() -> None:
    """map_exceptions() aborts with 400 for KeyError."""
    with pytest.raises(w_exceptions.BadRequest):
        flask_utils.map_exceptions(KeyError('missing'))


def test_map_exceptions_index_error() -> None:
    """map_exceptions() aborts with 404 for IndexError."""
    with pytest.raises(w_exceptions.NotFound):
        flask_utils.map_exceptions(IndexError('gone'))


def test_map_exceptions_value_error() -> None:
    """map_exceptions() aborts with 415 for ValueError."""
    with pytest.raises(w_exceptions.UnsupportedMediaType):
        flask_utils.map_exceptions(ValueError('bad value'))


def test_map_exceptions_not_implemented_error() -> None:
    """map_exceptions() aborts with 501 for NotImplementedError."""
    with pytest.raises(w_exceptions.NotImplemented):
        flask_utils.map_exceptions(NotImplementedError('nope'))


def test_map_exceptions_unknown_exception() -> None:
    """map_exceptions() aborts with 500 for unknown exception types."""
    with pytest.raises(w_exceptions.InternalServerError):
        flask_utils.map_exceptions(RuntimeError('oops'))


def test_map_exceptions_http_exception_passthrough() -> None:
    """map_exceptions() re-raises HTTPException instances directly."""
    with pytest.raises(w_exceptions.ImATeapot):
        flask_utils.map_exceptions(w_exceptions.ImATeapot('brew'))


def test_map_exceptions_dict_success() -> None:
    """map_exceptions() returns value for dict with status 200."""
    result = flask_utils.map_exceptions({'status': 200, 'value': 'ok'})
    assert result == 'ok'


def test_map_exceptions_dict_error() -> None:
    """map_exceptions() raises mapped exception for non-200 dict status."""
    with pytest.raises(ValueError, match='bad'):
        flask_utils.map_exceptions({'status': 415, 'value': 'bad'})


def test_map_exceptions_dict_unknown_status() -> None:
    """map_exceptions() raises generic Exception for unmapped status."""
    with pytest.raises(Exception, match='unknown'):
        flask_utils.map_exceptions({'status': 999, 'value': 'unknown'})
