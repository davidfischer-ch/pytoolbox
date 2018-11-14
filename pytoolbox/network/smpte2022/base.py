# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import struct

from fastxor import fast_xor_inplace

from pytoolbox import module
from pytoolbox.encoding import to_bytes
from pytoolbox.network.rtp import RtpPacket

_all = module.All(globals())


class FecPacket(object):
    """
    This represent a real-time transport protocol (RTP) packet.

    * :rfc:`2733`
    * `Wikipedia (RTP) <http://en.wikipedia.org/wiki/Real-time_Transport_Protocol>`_
    * `Parameters (RTP) <http://www.iana.org/assignments/rtp-parameters/rtp-parameters.xml>`_

    **Packet header**

    .. code-block:: text

         0                   1                   2                   3
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |       SNBase low bits         |        Length recovery        |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |E| PT recovery |                    Mask                       |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |                          TS recovery                          |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |N|D|type |index|    Offset     |      NA       |SNBase ext bits|
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

    The constructor will parse input bytes array to fill packet's fields.
    In case of error (e.g. bad version number) the constructor will abort filling fields and
    un-updated fields are set to their corresponding default value.

    :param bytes: Input array of bytes to parse as a RTP packet with FEC payload
    :type bytes: bytearray
    :param length: Amount of bytes to read from the array of bytes
    :type length: int
    :return: Generated RTP packet with SMPTE 2022-1 FEC payload (aka FEC packet)

    **Example usage**

    Testing header fields value (based on packet 3 of capture DCM_FEC_2D_6_10.pcap):

    * 1st row: RTP header, sequence = 37 798
    * 2nd row: FEC header, SN = 50 288, PT recovery = 0, TS recovery = 7850

    >>> header = bytearray.fromhex('806093a6 00000000 00000000 c4700000 80000000 00001eaa 00060a00')
    >>> length = 1344 - len(header)
    >>> print(length)
    1316
    >>> bytes = header + bytearray(length)
    >>> print(len(bytes))
    1344
    >>> fec = FecPacket(bytes, len(bytes))
    >>> assert(fec.valid)
    >>> print(fec)
    errors                = []
    sequence              = 37798
    algorithm             = XOR
    direction             = COL
    snbase                = 50288
    offset                = 6
    na                    = 10
    L x D                 = 6 x 10
    payload type recovery = 0
    timestamp recovery    = 7850
    length recovery       = 0
    payload recovery size = 1316
    missing               = []

    Testing header fields value (based on packet 5 of capture DCM_FEC_2D_6_10.pcap):

    * 1st row: RTP header, sequence = 63 004
    * 2nd row: FEC header, SN = 50 344, PT recovery = 0, TS recovery = 878

    >>> header = bytearray.fromhex('8060f61c 00000000 00000000 c4a80000 80000000 0000036e 40010600')
    >>> length = 1344 - len(header)
    >>> print(length)
    1316
    >>> bytes = header + bytearray(length)
    >>> print(len(bytes))
    1344
    >>> fec = FecPacket(bytes, len(bytes))
    >>> assert(fec.valid)
    >>> print(fec)
    errors                = []
    sequence              = 63004
    algorithm             = XOR
    direction             = ROW
    snbase                = 50344
    offset                = 1
    na                    = 6
    L x D                 = 6 x None
    payload type recovery = 0
    timestamp recovery    = 878
    length recovery       = 0
    payload recovery size = 1316
    missing               = []
    """

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Constants >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    ER_PAYLOAD_TYPE = 'RTP Header : Payload type must be set to 96'
    ER_EXTENDED = 'SMPTE 2022-1 Header : Extended must be set to one'
    ER_MASK = 'SMPTE 2022-1 Header : Mask must be set to zero'
    ER_N = 'SMPTE 2022-1 Header : N must be set to zero'
    ER_ALGORITHM = 'SMPTE 2022-1 Header : Algorithm must be set to XOR'
    ER_DIRECTION = 'SMPTE 2022-1 Header : Direction must be COL or ROW'
    ER_INDEX = 'SMPTE 2022-1 Header : Index must be set to zero'
    ER_LD = 'SMPTE 2022-1 Header : The following limitation failed : L*D <= 256'
    ER_L = 'SMPTE 2022-1 Header : The following limitation failed : 1 <= L <= 50'
    ER_D = 'SMPTE 2022-1 Header : The following limitation failed : 4 <= D <= 50'
    ER_PAYLOAD = "FEC packet must have a payload"
    ER_ALGORITHM = 'SMPTE 2022-1 Header : Only XOR FEC algorithm is handled'
    ER_VALID_MP2T = 'One of the packets is an invalid RTP packet (+expected MPEG2-TS payload)'
    ER_OFFSET = '(packets) Computed offset is out of range [1..255]'
    ER_SEQUENCE = "One of the packets doesn't verify : sequence = snbase + i * offset, 0<i<na"
    ER_INDEX = 'Unable to get missing media packet index'
    ER_J = 'Unable to find a suitable j e N that satisfy : media_sequence = snbase + j * offset'

    HEADER_LENGTH = 16
    E_MASK = 0x80
    PT_MASK = 0x7f
    N_MASK = 0x80
    D_MASK = 0x40
    T_MASK = 0x38
    T_SHIFT = 3
    I_MASK = 0x07
    SNBL_MASK = 0xffff
    SNBE_SHIFT = 16

    DIRECTION_NAMES = ('COL', 'ROW')
    DIRECTION_RANGE = xrange(len(DIRECTION_NAMES))  # noqa
    COL, ROW = DIRECTION_RANGE

    ALGORITHM_NAMES = ('XOR', 'Hamming', 'ReedSolomon')
    ALGORITHM_RANGE = xrange(len(ALGORITHM_NAMES))  # noqa
    XOR, Hamming, ReedSolomon = ALGORITHM_RANGE

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Properties >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    @property
    def valid(self):
        """Returns True if this packet is a valid RTP packet (with FEC payload)."""
        return len(self.errors) == 0

    @property
    def errors(self):
        """
        Returns an array containing any errors.

        :return: array of error message(s).

        **Example usage**

        Testing invalid header:

        #TODO >>> fec = FecPacket(bytearray(FecPacket.HEADER_LENGTH-1), FecPacket.HEADER_LENGTH-1)
        #TODO >>> print(fec.errors)
        #TODO ['RTP Header : Version must be set to 2', 'RTP packet must have a payload']
        """
        errors = self._errors
        if not self.extended:
            errors.append(FecPacket.ER_EXTENDED)
        if self.mask != 0:
            errors.append(FecPacket.ER_MASK)
        if self.n:
            errors.append(FecPacket.ER_N)
        if self.algorithm != FecPacket.XOR:
            errors.append(FecPacket.ER_ALGORITHM)
        if self.direction not in FecPacket.DIRECTION_RANGE:
            errors.append(FecPacket.ER_DIRECTION)
        if self.index != 0:
            errors.append(FecPacket.ER_INDEX)
        if self.payload_size == 0:
            errors.append(FecPacket.ER_PAYLOAD)
        if self.L < 1 or self.L > 50:
            errors.append(FecPacket.ER_L)
        if self.direction == FecPacket.COL and self.L * self.D > 256:
            errors.append(FecPacket.ER_LD)
        if self.direction == FecPacket.COL and (self.D < 4 or self.D > 50):
            errors.append(FecPacket.ER_D)
        return errors

    @property
    def D(self):
        """
        Returns the vertical size of the FEC matrix (rows).

        **Example usage**

        >>> packets = [RtpPacket.create(10, 100, RtpPacket.MP2T_PT, bytearray(123)),
        ...            RtpPacket.create(11, 200, RtpPacket.MP2T_PT, bytearray(1234))]
        >>> fec = FecPacket.compute(10, FecPacket.XOR, FecPacket.COL, 1, 2, packets)
        >>> print(fec.D)
        2
        """
        return self.na if self.direction == FecPacket.COL else None

    @property
    def L(self):
        """
        Returns the horizontal size of the FEC matrix (columns).

        **Example usage**

        >>> from pytoolbox.network.rtp import RtpPacket
        >>> packets = [RtpPacket.create(10, 100, RtpPacket.MP2T_PT, bytearray(123)),
        ...            RtpPacket.create(11, 200, RtpPacket.MP2T_PT, bytearray(1234))]
        >>> fec = FecPacket.compute(6, FecPacket.XOR, FecPacket.ROW, 2, 1, packets)
        >>> print(fec.L)
        2
        """
        return self.offset if self.direction == FecPacket.COL else self.na

    @property
    def header_size(self):
        """
        Returns the length (aka size) of the header.

        **Example usage**

        >>> from pytoolbox.network.rtp import RtpPacket
        >>> packets = [RtpPacket.create(10, 100, RtpPacket.MP2T_PT, bytearray(123)),
        ...            RtpPacket.create(11, 200, RtpPacket.MP2T_PT, bytearray(1234))]
        >>> fec = FecPacket.compute(1985, FecPacket.XOR, FecPacket.ROW, 2, 1, packets)
        >>> print(fec.header_size)
        16
        """
        return FecPacket.HEADER_LENGTH

    @property
    def payload_size(self):
        """
        Returns the length (aka size) of the payload.

        **Example usage**

        >>> from pytoolbox.network.rtp import RtpPacket
        >>> packets = [RtpPacket.create(10, 100, RtpPacket.MP2T_PT, bytearray(123)),
        ...            RtpPacket.create(11, 200, RtpPacket.MP2T_PT, bytearray(1234))]
        >>> fec = FecPacket.compute(27, FecPacket.XOR, FecPacket.ROW, 2, 1, packets)
        >>> print(fec.payload_size)
        1234
        """
        return len(self.payload_recovery) if self.payload_recovery else 0

    @property
    def header_bytes(self):
        """
        Returns SMPTE 2022-1 FEC header bytes.

        **Example usage**

        >>> from pytoolbox.network.rtp import RtpPacket
        >>> packets = [RtpPacket.create(10, 100, RtpPacket.MP2T_PT, bytearray(123)),
        ...            RtpPacket.create(11, 200, RtpPacket.MP2T_PT, bytearray(1234))]
        >>> fec = FecPacket.compute(26, FecPacket.XOR, FecPacket.ROW, 2, 1, packets)
        >>> print(fec)
        errors                = []
        sequence              = 26
        algorithm             = XOR
        direction             = ROW
        snbase                = 10
        offset                = 1
        na                    = 2
        L x D                 = 2 x None
        payload type recovery = 0
        timestamp recovery    = 172
        length recovery       = 1193
        payload recovery size = 1234
        missing               = []
        >>> fec_header = fec.header_bytes
        >>> assert(len(fec_header) == FecPacket.HEADER_LENGTH)
        >>> print(''.join(' %02x' % b for b in fec_header))
         00 0a 04 a9 80 00 00 00 00 00 00 ac 40 01 02 00
        >>> fec_header += fec.payload_recovery
        >>> rtp = RtpPacket.create(26, 100, RtpPacket.DYNAMIC_PT, fec_header)
        >>> rtp_header = rtp.header_bytes
        >>> header = rtp_header + fec_header
        >>> fec2 = FecPacket(header, len(header))
        >>> fec_header = fec2.header_bytes
        >>> assert(fec == fec2)
        """
        # FIXME map type string to enum
        bytes = bytearray(FecPacket.HEADER_LENGTH)
        struct.pack_into(b'!H', bytes, 0, self.snbase & FecPacket.SNBL_MASK)
        struct.pack_into(b'!H', bytes, 2, self.length_recovery)
        struct.pack_into(b'!I', bytes, 4, self.mask)
        bytes[4] = ((self.payload_type_recovery & FecPacket.PT_MASK) +
                    (FecPacket.E_MASK if self.extended else 0))
        struct.pack_into(b'!I', bytes, 8, self.timestamp_recovery)
        bytes[12] = ((self.N_MASK if self.n else 0) +
                     (self.D_MASK if self.direction else 0) +
                     ((self.algorithm << FecPacket.T_SHIFT) & self.T_MASK) +
                     (self.index & FecPacket.I_MASK))
        bytes[13] = self.offset
        bytes[14] = self.na
        bytes[15] = self.snbase >> FecPacket.SNBE_SHIFT
        return bytes

    @property
    def bytes(self):
        return self.header_bytes + self.payload_recovery

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Constructor >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def __init__(self, bytes=None, length=0):
        # Fields default values
        self._errors = []
        self.sequence = 0
        self.algorithm = FecPacket.XOR
        self.direction = FecPacket.COL
        self.snbase = 0
        self.offset = 0
        self.na = 0
        self.payload_type_recovery = 0
        self.timestamp_recovery = 0
        self.length_recovery = 0
        self.payload_recovery = []
        # (Unused has defined in SMPTE 2022-1-1)
        self.index = 0
        self.mask = 0
        self.extended = True
        self.n = False
        self.missing = []
        if bytes:
            packet = RtpPacket(bytes, length)
            self.sequence = packet.sequence
            self._errors = packet.errors
            if len(self._errors) > 0:
                return
            if packet.payload_type != RtpPacket.DYNAMIC_PT:
                self._errors.add(FecPacket.ER_PAYLOAD_TYPE)
                return
            self.snbase = (packet.payload[15]*256 + packet.payload[0])*256 + packet.payload[1]
            self.length_recovery = packet.payload[2]*256 + packet.payload[3]
            self.extended = (packet.payload[4] & FecPacket.E_MASK) != 0
            # if not self.extended:
            #     return
            self.payload_type_recovery = packet.payload[4] & FecPacket.PT_MASK
            self.mask = (packet.payload[5]*256 + packet.payload[6])*256 + packet.payload[7]
            # if self.mask != 0:
            #     return
            self.timestamp_recovery = (((packet.payload[8]*256 + packet.payload[9])*256 +
                                        packet.payload[10])*256 + packet.payload[11])
            self.n = (packet.payload[12] & FecPacket.N_MASK) != 0
            # if self.n:
            #     return
            self.direction = (packet.payload[12] & FecPacket.D_MASK) >> 6
            self.algorithm = packet.payload[12] & FecPacket.T_MASK
            # if self.algorithm != FecPacket.XOR:
            #     return
            self.index = packet.payload[12] & FecPacket.I_MASK
            # if self.index != 0:
            #     return
            self.offset = packet.payload[13]
            self.na = packet.payload[14]
            self.snbase += packet.payload[15] << 16
            # And finally ... The payload !
            self.payload_recovery = packet.payload[FecPacket.HEADER_LENGTH:]

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Functions >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    @staticmethod
    def compute(sequence, algorithm, direction, L, D, packets):
        """
        This method will generate FEC packet's field by applying FEC algorithm to input packets.
        In case of error (e.g. bad version number) the method will abort filling fields and
        un-updated fields are set to their corresponding default value.

        :param sequence: Sequence number of computed FEC packet
        :type sequence: int
        :param algorithm: Name of algorithm used to compute payload recovery from packets payload
        :type algorithm: str
        :param direction: Direction (column or row) of computed FEC packet (see RFC to understand)
        :type direction: str
        :param L: Horizontal size of the FEC matrix (columns)
        :type L: int
        :param D: Vertical size of the FEC matrix (rows)
        :type D: int
        :param packets: Array containing RTP packets to protect
        :type packets: array(RtPacket)

        **Example usage**

        Testing invalid input collection of packets:

        >>> from pytoolbox.network.rtp import RtpPacket
        >>> packets = [RtpPacket.create(10, 10, RtpPacket.MP2T_PT, 'a'),
        ...            RtpPacket.create(22, 22, RtpPacket.MP2T_PT, 'b')]
        >>> fec = FecPacket.compute(1, FecPacket.XOR, FecPacket.COL, 2, 2, packets)
        Traceback (most recent call last):
            ...
        ValueError: One of the packets doesn't verify : sequence = snbase + i * offset, 0<i<na

        Testing valid input collection of packets:

        >>> packets = [RtpPacket.create(10, 10, RtpPacket.MP2T_PT, bytearray('gaga', 'utf-8')),
        ...            RtpPacket.create(14, 14, RtpPacket.MP2T_PT, bytearray('salut', 'utf-8')),
        ...            RtpPacket.create(18, 18, RtpPacket.MP2T_PT, bytearray('12345', 'utf-8')),
        ...            RtpPacket.create(22, 22, RtpPacket.MP2T_PT, bytearray('robot', 'utf-8'))]
        >>> fec = FecPacket.compute(2, FecPacket.XOR, FecPacket.COL, 4, 4, packets)
        >>> print(fec)
        errors                = []
        sequence              = 2
        algorithm             = XOR
        direction             = COL
        snbase                = 10
        offset                = 4
        na                    = 4
        L x D                 = 4 x 4
        payload type recovery = 0
        timestamp recovery    = 0
        length recovery       = 1
        payload recovery size = 5
        missing               = []
        >>> print(''.join('%02x:' % x for x in fec.payload_recovery))
        57:5d:5a:4f:35:

        Testing fec packet generation (based on source RTP packets):

        >>> from os import urandom
        >>> from random import randint
        >>> from pytoolbox.network.rtp import RtpPacket
        >>> L = 4
        >>> D = 5
        >>> OFF = 2
        >>> # Generate a [D][L] matrix of randomly generated RTP packets
        >>> matrix = [[RtpPacket.create(L * j + i, (L * j + i) * 100 + randint(0, 50),
        ...           RtpPacket.MP2T_PT, bytearray(urandom(randint(50, 100))))
        ...           for i in xrange(L)] for j in xrange(D)]
        >>> assert(len(matrix) == D and len(matrix[0]) == L)
        >>> # Retrieve the OFF'th column of the matrix
        >>> expected_payload_type_recovery = 0
        >>> expected_timestamp_recovery = 0
        >>> expected_lenght_recovery = 0
        >>> expected_payload_recovery = bytearray(100)
        >>> packets = []
        >>> for i in xrange(D):
        ...     packet = matrix[i][OFF]
        ...     packets.append(packet)
        ...     # Compute expected recovery fields values
        ...     expected_payload_type_recovery ^= packet.payload_type
        ...     expected_timestamp_recovery ^= packet.timestamp
        ...     expected_lenght_recovery ^= packet.payload_size
        ...     for j in xrange(packet.payload_size):
        ...         expected_payload_recovery[j] ^= packet.payload[j]
        >>> fec = FecPacket.compute(15, FecPacket.XOR, FecPacket.COL, L, D, packets)
        >>> assert(fec.valid)
        >>> assert(fec.snbase == matrix[0][OFF].sequence == 2)
        >>> assert(fec.na == D and fec.offset == L)
        >>> assert(fec.payload_type_recovery == expected_payload_type_recovery)
        >>> assert(fec.timestamp_recovery == expected_timestamp_recovery)
        >>> assert(fec.length_recovery == expected_lenght_recovery)
        >>> for i in xrange(fec.payload_size):
        ...     if fec.payload_recovery[i] != expected_payload_recovery[i]:
        ...         print('Payload recovery test failed with i = ' + i)
        """
        # Fields default values
        fec = FecPacket()
        fec.sequence = sequence
        if algorithm not in FecPacket.ALGORITHM_RANGE:
            raise ValueError(to_bytes('algorithm is not a valid FEC algorithm'))
        if direction not in FecPacket.DIRECTION_RANGE:
            raise ValueError(to_bytes('direction is not a valid FEC direction'))
        fec.algorithm = algorithm
        fec.direction = direction
        if fec.direction == FecPacket.COL:
            fec.na = D
            fec.offset = L
        else:
            fec.na = L
            fec.offset = 1
        if fec.algorithm != FecPacket.XOR:
            raise NotImplementedError(to_bytes(FecPacket.ER_ALGORITHM))
        if len(packets) != fec.na:
            raise ValueError(to_bytes('packets must contain exactly {0} packets'.format(fec.na)))
        fec.snbase = packets[0].sequence
        # Detect maximum length of packets payload and check packets validity
        size = 0
        i = 0
        for packet in packets:
            if not packet.validMP2T:
                raise ValueError(to_bytes(FecPacket.ER_VALID_MP2T))
            if packet.sequence != (fec.snbase + i*fec.offset) % RtpPacket.S_MASK:
                raise ValueError(to_bytes(FecPacket.ER_SEQUENCE))
            size = max(size, packet.payload_size)
            i += 1
        # Create payload recovery field according to size/length
        fec.payload_recovery = bytearray(size)
        # Compute FEC packet's fields based on input packets
        for packet in packets:
            # Update (...) recovery fields by xor'ing corresponding fields of all packets
            fec.payload_type_recovery ^= packet.payload_type
            fec.timestamp_recovery ^= packet.timestamp
            fec.length_recovery ^= packet.payload_size
            # Update payload recovery by xor'ing all packets payload
            payload = packet.payload
            if len(packet.payload) < size:
                payload = payload + bytearray(size - len(packet.payload))
            fast_xor_inplace(fec.payload_recovery, payload)
            # NUMPY fec.payload_recovery = bytearray(
            #     numpy.bitwise_xor(fec.payload_recovery, payload))
            # XOR LOOP for i in xrange(min(size, len(packet.payload))):
            # XOR LOOP     fec.payload_recovery[i] ^= packet.payload[i]
        return fec

    def set_missing(self, media_sequence):
        """
        Register a protected media packet as missing.

        **Example usage**

        >>> packets = [
        ...     RtpPacket.create(65530, 65530, RtpPacket.MP2T_PT, bytearray('gaga', 'utf-8')),
        ...     RtpPacket.create(65533, 65533, RtpPacket.MP2T_PT, bytearray('salut', 'utf-8')),
        ...     RtpPacket.create(    1,     1, RtpPacket.MP2T_PT, bytearray('12345', 'utf-8')),
        ...     RtpPacket.create(    4,     4, RtpPacket.MP2T_PT, bytearray('robot', 'utf-8'))
        ... ]
        >>> fec = FecPacket.compute(4, FecPacket.XOR, FecPacket.COL, 3, 4, packets)
        >>> print(fec)
        errors                = []
        sequence              = 4
        algorithm             = XOR
        direction             = COL
        snbase                = 65530
        offset                = 3
        na                    = 4
        L x D                 = 3 x 4
        payload type recovery = 0
        timestamp recovery    = 2
        length recovery       = 1
        payload recovery size = 5
        missing               = []

        Testing that bad input values effectively throws an exception:

        >>> fec.set_missing(fec.snbase + fec.offset + 1)
        Traceback (most recent call last):
            ...
        ValueError: Unable to find a suitable j e N that satisfy : media_sequence = snbase + j * offset
        >>> fec.set_recovered(-1)
        Traceback (most recent call last):
            ...
        ValueError: Unable to find a suitable j e N that satisfy : media_sequence = snbase + j * offset

        Testing set / get of a unique missing value:

        >>> print(fec.set_missing(1))
        2
        >>> print(fec.missing[0])
        1
        >>> print(len(fec.missing))
        1

        Testing simple recovery of a unique value:

        >>> print(fec.set_recovered(1))
        2
        >>> print(len(fec.missing))
        0

        Testing set / get of multiple missing values (including re-setting of a value):

        >>> print(fec.set_missing(4))
        3
        >>> print(fec.set_missing(4))
        3
        >>> print(len(fec.missing))
        1
        >>> print(fec.set_missing(fec.snbase + fec.offset))
        1
        >>> print(fec.set_missing(fec.snbase))
        0
        >>> print(len(fec.missing))
        3
        >>> print(fec.missing)
        [4, 65533, 65530]

        Testing re-recovery of a value:

        >>> fec.set_recovered(4); fec.set_recovered(4)
        Traceback (most recent call last):
            ...
        ValueError: list.remove(x): x not in list
        >>> print(fec.missing)
        [65533, 65530]
        """
        j = self.computeJ(media_sequence)
        if j is None:
            raise ValueError(FecPacket.ER_J)
        if media_sequence not in self.missing:
            self.missing.append(media_sequence)
        return j

    def set_recovered(self, media_sequence):
        """
        TODO
        """
        j = self.computeJ(media_sequence)
        if j is None:
            raise ValueError(FecPacket.ER_J)
        self.missing.remove(media_sequence)
        return j

    def computeJ(self, media_sequence):
        """
        TODO
        """
        delta = media_sequence - self.snbase
        if delta < 0:
            delta = RtpPacket.S_MASK + delta
        if delta % self.offset != 0:
            return None
        return int(delta / self.offset)

    def __eq__(self, other):
        """
        Test equality field by field !
        """
        if isinstance(other, self.__class__):
            return (self.sequence == other.sequence and self.algorithm == other.algorithm and
                    self.direction == other.direction and self.snbase == other.snbase and
                    self.offset == other.offset and self.na == other.na and
                    self.payload_type_recovery == other.payload_type_recovery and
                    self.length_recovery == other.length_recovery and
                    self.payload_recovery == other.payload_recovery)

    def __str__(self):
        """
        Returns a string containing a formated representation of the packet fields.

        **Example usage**

        >>> packets = [RtpPacket.create(10, 100, RtpPacket.MP2T_PT, bytearray(10)),
        ...            RtpPacket.create(11, 200, RtpPacket.MP2T_PT, bytearray(5)),
        ...            RtpPacket.create(12, 300, RtpPacket.MP2T_PT, bytearray(7)),
        ...            RtpPacket.create(13, 400, RtpPacket.MP2T_PT, bytearray(10))]
        >>> fec = FecPacket.compute(12, FecPacket.XOR, FecPacket.ROW, 4, 1, packets)
        >>> print(fec)
        errors                = []
        sequence              = 12
        algorithm             = XOR
        direction             = ROW
        snbase                = 10
        offset                = 1
        na                    = 4
        L x D                 = 4 x None
        payload type recovery = 0
        timestamp recovery    = 16
        length recovery       = 2
        payload recovery size = 10
        missing               = []

        >>> fec = FecPacket.compute(14, FecPacket.XOR, FecPacket.COL, 1, 4, packets)
        >>> print(fec)
        errors                = []
        sequence              = 14
        algorithm             = XOR
        direction             = COL
        snbase                = 10
        offset                = 1
        na                    = 4
        L x D                 = 1 x 4
        payload type recovery = 0
        timestamp recovery    = 16
        length recovery       = 2
        payload recovery size = 10
        missing               = []
        """
        return ("""errors                = {0.errors}
sequence              = {0.sequence}
algorithm             = {1}
direction             = {2}
snbase                = {0.snbase}
offset                = {0.offset}
na                    = {0.na}
L x D                 = {0.L} x {0.D}
payload type recovery = {0.payload_type_recovery}
timestamp recovery    = {0.timestamp_recovery}
length recovery       = {0.length_recovery}
payload recovery size = {0.payload_size}
missing               = {0.missing}""".format(self, FecPacket.ALGORITHM_NAMES[self.algorithm],
                                              FecPacket.DIRECTION_NAMES[self.direction]))


__all__ = _all.diff(globals())
