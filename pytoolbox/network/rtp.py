from __future__ import annotations

import struct

__all__ = ['RtpPacket']


class RtpPacket(object):  # pylint:disable=too-many-instance-attributes
    """
    This represent a real-time transport protocol (RTP) packet.

    * :rfc:`3550`
    * `Wikipedia (RTP) <http://en.wikipedia.org/wiki/Real-time_Transport_Protocol>`_
    * `Parameters (RTP) <http://www.iana.org/assignments/rtp-parameters/rtp-parameters.xml>`_

    **Packet header**

    * RFC 3550 page 13

    .. code-block:: text

        0                   1                   2                   3
        0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |V=2|P|X|  CC   |M|     PT      |       sequence number         |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |                           timestamp                           |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
       |           synchronization source (SSRC) identifier            |
       +=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
       |            contributing source (CSRC) identifiers             |
       |                             ....                              |
       +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

    **Extension header**

    * RFC 3550 page 19

    .. code-block:: text

         0                   1                   2                   3
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |      defined by profile       |           length              |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                        header extension                       |
        |                             ....                              |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    """

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Constants >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    ER_VERSION = 'RTP Header : Version must be set to 2'
    ER_PADDING_LENGTH = 'RTP Header : Bad padding length'
    ER_EXTENSION_LENGTH = 'RTP Header : Bad extension length'
    ER_PAYLOAD = 'RTP packet must have a payload'

    HEADER_LENGTH = 12
    V_MASK = 0xc0
    V_SHIFT = 6
    P_MASK = 0x20
    X_MASK = 0x10
    CC_MASK = 0x0f
    M_MASK = 0x80
    PT_MASK = 0x7f
    DYNAMIC_PT = 96   # Dynamic payload type
    MP2T_PT = 33      # MPEG2 TS payload type
    MP2T_CLK = 90000  # MPEG2 TS clock rate [Hz]
    S_MASK = 0x0000ffff
    TS_MASK = 0xffffffff

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Properties >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    @property
    def valid(self):
        """Returns True if this packet is a valid RTP packet."""
        return len(self.errors) == 0

    @property
    def validMP2T(self):  # pylint:disable=invalid-name
        """Returns True if this packet is a valid RTP packet containing a MPEG2-TS payload."""
        return self.valid and self.payload_type == self.MP2T_PT

    @property
    def errors(self):
        """
        Returns an array containing any errors.

        :return: array of error message(s).

        **Example usage**

        Testing invalid header:

        >>> from pytoolbox.unittest import asserts
        >>> rtp = RtpPacket(bytearray(RtpPacket.HEADER_LENGTH-1), RtpPacket.HEADER_LENGTH-1)
        >>> asserts.list_equal(rtp.errors, [
        ...     'RTP Header : Version must be set to 2',
        ...     'RTP packet must have a payload'
        ... ])

        Testing a valid RTP packet with a MPEG2-TS payload:

        >>> rtp = RtpPacket.create(6, 777, RtpPacket.MP2T_PT, 'salut')
        >>> asserts.list_equal(rtp.errors, [])
        """
        errors = []
        if self._error:
            errors.append(self._error)
        if self.version != 2:
            errors.append(self.ER_VERSION)
        if self.payload_size == 0:
            errors.append(self.ER_PAYLOAD)
        return errors

    @property
    def clock_rate(self):
        """Return the MPEG2-TS clock rate of a MPEG2-TS payload or 1 if this is not."""
        return self.MP2T_CLK if self.payload_type == self.MP2T_PT else 1

    @property
    def header_size(self):
        """
        Returns the length (aka size) of the header.

        **Example usage**

        >>> rtp = RtpPacket.create(6, 777, RtpPacket.MP2T_PT, 'salut')
        >>> print(rtp.header_size)
        12
        """
        return self.HEADER_LENGTH + 4 * len(self.csrc)

    @property
    def payload_size(self):
        """
        Returns the length (aka size) of the payload.

        **Example usage**

        >>> rtp = RtpPacket.create(6, 777, RtpPacket.MP2T_PT, 'salut')
        >>> print(rtp.payload_size)
        5
        """
        return len(self.payload) if self.payload else 0

    @property
    def time(self):
        """Return computed time (*timestamp / clock rate*)."""
        return self.timestamp / self.clock_rate

    @property
    def header_bytes(self):
        """
        Return the RTP header bytes.

        *Example usage*

        >>> rtp = RtpPacket.create(6, 777, RtpPacket.MP2T_PT, bytearray.fromhex('00 01 02 03'))
        >>> print(rtp)
        version      = 2
        errors       = []
        padding      = False
        extension    = False
        marker       = False
        payload type = 33
        sequence     = 6
        timestamp    = 777
        clock rate   = 90000
        time         = 0
        ssrc         = 0
        csrc count   = 0
        payload size = 4
        >>> header = rtp.header_bytes
        >>> assert len(header) == 12
        >>> print(''.join(' %02x' % b for b in header))
         80 21 00 06 00 00 03 09 00 00 00 00
        >>> header += rtp.payload
        >>> assert rtp == RtpPacket(header, len(header))

        >>> rtp = RtpPacket.create(0xffffffff, 0xffffffffff, RtpPacket.DYNAMIC_PT, bytearray(1023))
        >>> print(rtp)
        version      = 2
        errors       = []
        padding      = False
        extension    = False
        marker       = False
        payload type = 96
        sequence     = 65535
        timestamp    = 4294967295
        clock rate   = 1
        time         = 4294967295
        ssrc         = 0
        csrc count   = 0
        payload size = 1023
        >>> header = rtp.header_bytes
        >>> assert len(header) == 12
        >>> print(''.join(' %02x' % b for b in header))
         80 60 ff ff ff ff ff ff 00 00 00 00
        >>> header += rtp.payload
        >>> assert rtp == RtpPacket(header, len(header))
        """
        cc = len(self.csrc)  # pylint:disable=invalid-name
        header = bytearray(self.HEADER_LENGTH + 4 * cc)
        header[0] = (
            ((self.version << self.V_SHIFT) & self.V_MASK)
            + (self.P_MASK if self.padding else 0)
            + (self.X_MASK if self.extension else 0)
            + (cc & self.CC_MASK))
        header[1] = (
            (self.M_MASK if self.marker else 0)
            + (self.payload_type & self.PT_MASK))
        struct.pack_into(b'!H', header, 2, self.sequence)
        struct.pack_into(b'!I', header, 4, self.timestamp)
        struct.pack_into(b'!I', header, 8, self.ssrc)
        i = 12
        for contributor in self.csrc:
            struct.pack_into(b'!I', header, i, contributor)
            i += 4
        return header

    @property
    def bytes(self):
        """Return the RTP packet header and payload bytes."""
        return self.header_bytes + self.payload

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Constructor >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def __init__(self, data, length):
        """
        This constructor will parse input bytes array to fill packet's fields.
        In case of error (e.g. bad version number) the constructor will abort filling
        fields and un-updated fields are set to their corresponding default value.

        :param bytes: Input array of bytes to parse as a RTP packet
        :type bytes: bytearray
        :param length: Amount of bytes to read from the array of bytes
        :type length: int

        **Example usage**

        Testing invalid headers:

        >>> rtp = RtpPacket(bytearray(RtpPacket.HEADER_LENGTH-1), RtpPacket.HEADER_LENGTH-1)
        >>> rtp.valid  # Bad length
        False
        >>> rtp = RtpPacket(bytearray(RtpPacket.HEADER_LENGTH), RtpPacket.HEADER_LENGTH)
        >>> rtp.valid  # Bad version
        False
        >>> bytes = bytearray(RtpPacket.HEADER_LENGTH)
        >>> bytes[0] = 0xa0
        >>> rtp = RtpPacket(bytes, RtpPacket.HEADER_LENGTH)
        >>> rtp.valid  # Padding enabled but not present
        False

        Testing header fields value:

        >>> bytes = bytes.fromhex('80 a1 a4 25 ca fe b5 04 b0 60 5e bb 12 34')
        >>> rtp = RtpPacket(bytes, len(bytes))
        >>> rtp.valid
        True
        >>> print(rtp)
        version      = 2
        errors       = []
        padding      = False
        extension    = False
        marker       = True
        payload type = 33
        sequence     = 42021
        timestamp    = 3405690116
        clock rate   = 90000
        time         = 37841
        ssrc         = 2959105723
        csrc count   = 0
        payload size = 2
        >>> rtp.csrc
        []
        >>> rtp.payload[0]
        18
        >>> rtp.payload[1]
        52

        Testing header fields value (with padding, extension and ccrc):

        >>> bytes = bytes.fromhex('b5a1a401 cafea421 b0605ebb 11111111 22222222 33333333 '
        ...                       '44444444 55555555 00000004 87654321 12340002')
        >>> rtp = RtpPacket(bytes, len(bytes))
        >>> rtp.valid
        True
        >>> rtp.version
        2
        >>> rtp.padding
        True
        >>> rtp.extension
        True
        >>> rtp.marker
        True
        >>> rtp.payload_type
        33
        >>> rtp.sequence
        41985
        >>> rtp.timestamp
        3405685793
        >>> rtp.clock_rate
        90000
        >>> rtp.ssrc
        2959105723
        >>> len(rtp.csrc)
        5
        >>> rtp.csrc
        [286331153, 572662306, 858993459, 1145324612, 1431655765]
        >>> rtp.payload
        bytearray(b'\\x124')
        """

        # Fields default values
        self.version = 0
        self.padding = False
        self.extension = False
        self.marker = False
        self.payload_type = 0
        self.sequence = 0
        self.timestamp = 0
        self.ssrc = 0
        self.csrc = []
        self.payload = []
        self._error = None

        offset = self.HEADER_LENGTH
        if length < offset:
            return

        self.version = (data[0] & self.V_MASK) >> 6
        if self.version != 2:
            return

        self.padding = (data[0] & self.P_MASK) == self.P_MASK
        if self.padding:  # Remove padding if present
            padding_length = data[-1]
            if padding_length == 0 or length < (offset + padding_length):
                self._error = self.ER_PADDING_LENGTH
                return
            length -= padding_length

        self.extension = (data[0] & self.X_MASK) == self.X_MASK
        cc = data[0] & self.CC_MASK  # pylint:disable=invalid-name
        self.csrc = []  # cc > 0 ? new long[cc] : null
        self.marker = (data[1] & self.M_MASK) == self.M_MASK
        self.payload_type = data[1] & self.PT_MASK
        self.sequence = data[2] * 256 + data[3]
        self.timestamp = ((data[4] * 256 + data[5]) * 256 + data[6]) * 256 + data[7]
        self.ssrc = ((data[8] * 256 + data[9]) * 256 + data[10]) * 256 + data[11]

        for _ in range(cc):
            self.csrc.append(
                ((data[offset] * 256 + data[offset + 1]) * 256 + data[offset + 2]) * 256
                + data[offset + 3])
            offset += 4
            # FIXME In session.c of VLC they store per-source statistics in a rtp_source_t struct

        if self.extension:  # Extension header (ignored for now)
            extension_length = data[offset + 2] * 256 + data[offset + 3]
            offset += 4 + extension_length
            if length < offset:
                self._error = self.ER_EXTENSION_LENGTH
                return

        # And finally ... The payload !
        self.payload = data[offset:length]

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Functions >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

#    public int compareTo(RtpPacket pPacket):
#        BEFORE = -1
#        EQUAL   = 0
#        AFTER   = 1

#        # This optimization is usually worthwhile, and can always be added
#        if (this == pPacket) return EQUAL
#        if (this.sequence < pPacket.sequence) return BEFORE
#        if (this.sequence > pPacket.sequence) return AFTER
#        return EQUAL

    @classmethod
    def create(cls, sequence, timestamp, payload_type, payload):
        """
        Create a valid RTP packet with a given payload.

        :param sequence: Packet sequence number (16 bits)
        :type sequence: int
        :param timestamp: Packet timestamp (32 bits)
        :type timestamp: int
        :param payload_type: Packet payload type (7 bits)
        :type payload_type: int
        :param payload: Packet payload, can be an array of bytes or a string
        :type payload: bytearray

        **Example usage**

        >>> p = RtpPacket.create(10, 1024, RtpPacket.MP2T_PT, 'The payload string')
        >>> q = RtpPacket.create(11, 1028, RtpPacket.MP2T_PT, bytearray.fromhex('00 11 22 33'))
        >>> r = RtpPacket.create(11, 1028, RtpPacket.DYNAMIC_PT, bytearray.fromhex('cc aa ff ee'))
        >>> assert p.validMP2T and q.validMP2T and r.valid
        """
        rtp = cls(None, 0)
        rtp.version = 2
        rtp.padding = False
        rtp.extension = False
        rtp.marker = False
        rtp.payload_type = payload_type & cls.PT_MASK
        rtp.sequence = sequence & cls.S_MASK
        rtp.timestamp = timestamp & cls.TS_MASK
        rtp.ssrc = 0
        rtp.csrc = []
        rtp.payload = payload
        return rtp

    def __eq__(self, other):
        """
        Equality test.

        .. warning::

            Test equality only on some fields (not all) !
        """
        return (
            isinstance(other, self.__class__)
            and self.sequence == other.sequence
            and self.timestamp == other.timestamp
            and self.payload_type == other.payload_type
            and self.payload == other.payload)

    def __str__(self):
        """
        Returns a string containing a formated representation of the packet fields.

        **Example usage**

        >>> rtp = RtpPacket.create(6, 777, RtpPacket.MP2T_PT, 'salut les loulous')
        >>> print(rtp)
        version      = 2
        errors       = []
        padding      = False
        extension    = False
        marker       = False
        payload type = 33
        sequence     = 6
        timestamp    = 777
        clock rate   = 90000
        time         = 0
        ssrc         = 0
        csrc count   = 0
        payload size = 17
        """
        return f"""version      = {self.version}
errors       = {self.errors}
padding      = {self.padding}
extension    = {self.extension}
marker       = {self.marker}
payload type = {self.payload_type}
sequence     = {self.sequence}
timestamp    = {self.timestamp}
clock rate   = {self.clock_rate}
time         = {self.time:.0f}
ssrc         = {self.ssrc}
csrc count   = {len(self.csrc)}
payload size = {self.payload_size}"""
