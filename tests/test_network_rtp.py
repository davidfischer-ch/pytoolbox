"""Tests for the RTP packet."""

from __future__ import annotations

from pytoolbox.network.rtp import RtpPacket


def test_csrc_count_beyond_the_data_is_invalid() -> None:
    """A CSRC count asking for more bytes than the datagram holds makes the packet invalid."""
    data = bytearray(b'\x8f' + bytes(11))

    assert RtpPacket(data, len(data)).valid is False


def test_extension_header_beyond_the_data_is_invalid() -> None:
    """An extension bit set on a datagram ending at the fixed header makes the packet invalid."""
    data = bytearray(b'\x90' + bytes(11))

    assert RtpPacket(data, len(data)).valid is False


def test_padding_length_is_read_at_the_end_of_the_packet() -> None:
    """The padding length is the last byte of the packet, not of a longer buffer holding it."""
    data = bytearray(b'\xa0\x21' + bytes(10) + b'payload\x01' + b'\xff' * 8)

    packet = RtpPacket(data, len(data) - 8)

    assert packet.valid is True
    assert packet.payload == b'payload'
