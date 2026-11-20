"""Tests for the SMPTE 2022-1 FEC receiver."""

# pylint:disable=use-implicit-booleaness-not-comparison
from __future__ import annotations

import io

from pytoolbox.network.rtp import RtpPacket
from pytoolbox.network.smpte2022.base import FecPacket
from pytoolbox.network.smpte2022.receiver import FecReceiver

from .test_network_smpte2022_base import create_fec_datagram


def create_column_fec(sequence: int, snbase: int) -> FecPacket:
    """Return a column FEC packet protecting the 4 media packets from ``snbase``."""
    return FecPacket.compute(
        sequence,
        FecPacket.XOR,
        FecPacket.COL,
        1,
        4,
        [create_media((snbase + index) & RtpPacket.S_MASK) for index in range(4)],
    )


def create_media(sequence: int) -> RtpPacket:
    """Return an MPEG2-TS media packet, its payload naming its sequence."""
    return RtpPacket.create(
        sequence,
        sequence * 100,
        RtpPacket.MP2T_PT,
        bytearray(f'#{sequence}', 'ascii'),
    )


def create_receiver(delay: int) -> tuple[FecReceiver, io.BytesIO]:
    """Return a receiver delaying ``delay`` media packets, and its output."""
    output = io.BytesIO()
    receiver = FecReceiver(output)
    receiver.set_delay(delay, FecReceiver.PACKETS)
    return receiver, output


def test_recovery_aborts_on_a_protected_packet_already_written() -> None:
    """
    A FEC packet left needing a packet already written out is dropped, and the stream goes on.
    """
    receiver, output = create_receiver(4)
    receiver.put_media(create_media(10), True)
    receiver.put_media(create_media(11), True)
    receiver.put_fec(create_column_fec(5, 10))
    for sequence in (14, 15, 16):
        receiver.put_media(create_media(sequence), True)

    receiver.put_media(create_media(12), True)

    assert receiver.media_aborted_recovery == 1
    assert receiver.media_recovered == 0
    assert receiver.cols == {}
    assert receiver.crosses == {}
    receiver.flush()
    assert output.getvalue() == b'#10#11#12#14#15#16'


def test_recovery_cascades_onto_media_sequence_zero() -> None:
    """Media packet n°0, reached at each wraparound, is recovered like any other."""
    receiver, _ = create_receiver(2)
    for sequence in (65532, 65533, 65534, 65535):
        receiver.put_media(create_media(sequence), True)
    receiver.put_fec(create_column_fec(5, 65534))

    receiver.put_media(create_media(1), True)

    assert receiver.media_recovered == 1
    assert receiver.medias[0].payload == create_media(0).payload


def test_recovery_by_fec_sequence_zero() -> None:
    """FEC packet n°0, reached at each wraparound, recovers like any other."""
    receiver, _ = create_receiver(2)
    for sequence in (65532, 65533, 65534, 65535):
        receiver.put_media(create_media(sequence), True)
    receiver.put_fec(create_column_fec(0, 65534))

    receiver.put_media(create_media(0), True)

    assert receiver.media_recovered == 1
    assert receiver.medias[1].payload == create_media(1).payload
    assert receiver.cols == {}


def test_put_fec_protects_16_bit_media_sequences() -> None:
    """The SNBase extension bits never take a FEC packet off the 16-bit media sequences."""
    receiver, _ = create_receiver(4)
    data = create_fec_datagram(direction=FecPacket.ROW, offset=1, na=5, snbase=0x1000A)

    receiver.put_fec(FecPacket(data, len(data)))

    assert sorted(receiver.crosses) == [10, 11, 12, 13, 14]


def test_put_media_drops_a_packet_already_written() -> None:
    """A media packet behind the output position is dropped, never held until the wraparound."""
    receiver, output = create_receiver(4)
    for sequence in range(100, 111):
        receiver.put_media(create_media(sequence), True)
    assert receiver.position == 106

    receiver.put_media(RtpPacket.create(100, 0, RtpPacket.MP2T_PT, bytearray(b'stale')), True)

    assert sorted(receiver.medias) == [107, 108, 109, 110]
    assert receiver.position == 106
    assert receiver.media_dropped == 1
    for sequence in range(111, 121):
        receiver.put_media(create_media(sequence), True)
    receiver.flush()
    assert output.getvalue() == b''.join(create_media(s).payload for s in range(100, 121))
