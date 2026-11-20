"""Tests for the SMPTE 2022-1 FEC packet."""

from __future__ import annotations

import struct

from pytoolbox.network.rtp import RtpPacket
from pytoolbox.network.smpte2022.base import FecPacket


def create_fec_datagram(*, direction: int, offset: int, na: int, snbase: int) -> bytearray:
    """Return a FEC datagram, its SNBase on 24 bits split into its low and its extension bits."""
    rtp_header = struct.pack('!BBHII', 0x80, RtpPacket.DYNAMIC_PT, 7, 0, 0)
    fec_header = struct.pack(
        '!HHB3sIBBBB',
        snbase & 0xFFFF,
        0,
        FecPacket.E_MASK,
        bytes(3),
        0,
        direction << 6,
        offset,
        na,
        snbase >> 16,
    )
    return bytearray(rtp_header + fec_header + b'payload')


def test_snbase_extension_bits_round_trip() -> None:
    """The SNBase extension bits count once, and the header writes back the bytes read."""
    data = create_fec_datagram(direction=FecPacket.ROW, offset=1, na=5, snbase=0x1000A)

    fec = FecPacket(data, len(data))

    assert fec.snbase == 0x1000A
    assert (
        fec.header_bytes
        == data[RtpPacket.HEADER_LENGTH : RtpPacket.HEADER_LENGTH + FecPacket.HEADER_LENGTH]
    )


def test_offset_zero_is_invalid() -> None:
    """An offset of zero protects no media packet but the first, over and over."""
    data = create_fec_datagram(direction=FecPacket.ROW, offset=0, na=5, snbase=10)

    assert FecPacket(data, len(data)).valid is False


def test_payload_shorter_than_the_header_is_invalid() -> None:
    """A FEC payload too short to hold the SMPTE 2022-1 header makes the packet invalid."""
    data = bytearray(RtpPacket.create(7, 0, RtpPacket.DYNAMIC_PT, bytearray(4)).bytes)

    assert FecPacket(data, len(data)).valid is False
