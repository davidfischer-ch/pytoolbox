"""Tests for the crypto module."""

from __future__ import annotations

from base64 import b64decode

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from pytoolbox import crypto


def test_generate_rsa_key_pair_pem_headers() -> None:
    """Verify RSA key pair has correct PEM headers."""
    private_pem, public_pem = crypto.generate_rsa_key_pair()
    assert private_pem.startswith('-----BEGIN RSA PRIVATE KEY-----')
    assert private_pem.strip().endswith('-----END RSA PRIVATE KEY-----')
    assert public_pem.startswith('-----BEGIN PUBLIC KEY-----')
    assert public_pem.strip().endswith('-----END PUBLIC KEY-----')


def test_generate_rsa_key_pair_loadable() -> None:
    """Verify generated RSA key pair can be loaded by cryptography library."""
    private_pem, public_pem = crypto.generate_rsa_key_pair()
    serialization.load_pem_private_key(private_pem.encode(), password=None)
    serialization.load_pem_public_key(public_pem.encode())


def test_generate_rsa_key_pair_unique() -> None:
    """Verify each generated RSA key pair is unique."""
    first_private, _ = crypto.generate_rsa_key_pair()
    second_private, _ = crypto.generate_rsa_key_pair()
    assert first_private != second_private


def test_generate_rsa_key_pair_bits() -> None:
    """Verify RSA key pair is generated with the specified key size."""
    private_pem, _ = crypto.generate_rsa_key_pair(bits=4096)
    private_key = serialization.load_pem_private_key(private_pem.encode(), password=None)
    assert private_key.key_size == 4096  # type: ignore[union-attr]


def test_sign_rsa_approval_token() -> None:
    """Verify RSA-signed token can be verified with the public key."""
    private_pem, public_pem = crypto.generate_rsa_key_pair()
    token = 'some-approval-token'
    signature = crypto.sign_rsa_approval_token(private_pem, token)
    public_key = serialization.load_pem_public_key(public_pem.encode())
    public_key.verify(  # type: ignore[union-attr]
        b64decode(signature),
        token.encode('ascii'),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )


def test_sign_rsa_approval_token_is_base64() -> None:
    """Verify the signature is valid base64 with expected length."""
    private_pem, _ = crypto.generate_rsa_key_pair()
    signature = crypto.sign_rsa_approval_token(private_pem, 'token')
    decoded = b64decode(signature)
    assert len(decoded) == 256  # 2048-bit key → 256-byte signature


def test_sign_rsa_approval_token_invalid_key() -> None:
    """Verify signing with invalid key raises an exception."""
    with pytest.raises(Exception):
        crypto.sign_rsa_approval_token('not-a-pem-key', 'token')
