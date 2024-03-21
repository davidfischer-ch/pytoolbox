from __future__ import annotations

from pytoolbox.network.rtp import RtpPacket

from .base import FecPacket

__all__ = ['FecGenerator']


class FecGenerator(object):  # pylint:disable=too-many-instance-attributes
    """
    A SMPTE 2022-1 FEC streams generator.
    This generator accept incoming RTP media packets and compute corresponding FEC packets.
    """

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Properties >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    @property
    def L(self):  # pylint:disable=invalid-name
        """
        Returns the Horizontal size of the FEC matrix (columns).

        **Example usage**

        >>> print(FecGenerator(4, 5).L)
        4
        """
        return self._L

    @property
    def D(self):  # pylint:disable=invalid-name
        """
        Returns the vertical size of the FEC matrix (rows).

        **Example usage**

        >>> print(FecGenerator(4, 5).D)
        5
        """
        return self._D

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Constructor >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def __init__(self, L: int, D: int):  # pylint:disable=invalid-name,too-many-instance-attributes
        """
        Construct a FecGenerator.

        :param L: Horizontal size of the FEC matrix (columns)
        :param D: Vertical size of the FEC matrix (rows)
        """
        self._L, self._D = L, D  # pylint:disable=invalid-name
        self._col_sequence = self._row_sequence = 1
        self._media_sequence = None
        self._medias = []
        self._invalid = self._total = 0

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Functions >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    @staticmethod
    def on_new_col(col: FecPacket):
        """
        Called by FecGenerator when a new column FEC packet is generated and available for output.

        By default this method only print a message to `stdout`.

        .. seealso::

            You can `monkey patch <http://stackoverflow.com/questions/5626193>`_ it.

        :param col: Generated column FEC packet
        """
        print(
            f'New COL FEC packet '
            f'seq={col.sequence} '
            f'snbase={col.snbase} '
            f'LxD={col.L}x{col.D} '
            f'trec={col.timestamp_recovery}')

    @staticmethod
    def on_new_row(row: FecPacket):
        """
        Called by FecGenerator when a new row FEC packet is generated and available for output.

        By default this method only print a message to `stdout`.

        .. seealso::

            You can `monkey patch <http://stackoverflow.com/questions/5626193>`_ it.

        :param row: Generated row FEC packet
        """
        print(
            f'New ROW FEC packet '
            f'seq={row.sequence} '
            f'snbase={row.snbase} '
            f'LxD={row.L}x{row.D} '
            f'trec={row.timestamp_recovery}')

    def on_reset(self, media: RtpPacket):
        """
        Called by FecGenerator when the algorithm is reseted (an incoming media is out of sequence).

        By default this method only print a message to `stdout`.

        .. seealso::

            You can `monkey patch <http://stackoverflow.com/questions/5626193>`_ it.

        :param media: Out of sequence media packet
        """
        print(
            f'Media seq={media.sequence} is out of sequence '
            f'(expected {self._media_sequence}) : FEC algorithm reseted !')

    def put_media(self, media: RtpPacket):
        """
        Put an incoming media packet.

        :param media: Incoming media packet

        **Example usage**

        Testing input of out of sequence medias:

        >>> g = FecGenerator(4, 5)
        >>> R = RtpPacket
        >>> g.put_media(R.create(1, 100, R.MP2T_PT, bytearray('Tabby', 'utf-8')))
        Media seq=1 is out of sequence (expected None) : FEC algorithm reseted !
        >>> g.put_media(R.create(1, 100, R.MP2T_PT, bytearray('1234', 'utf-8')))
        Media seq=1 is out of sequence (expected 2) : FEC algorithm reseted !
        >>> g.put_media(R.create(4, 400, R.MP2T_PT, bytearray('abcd', 'utf-8')))
        Media seq=4 is out of sequence (expected 2) : FEC algorithm reseted !
        >>> g.put_media(R.create(2, 200, R.MP2T_PT, bytearray('python', 'utf-8')))
        Media seq=2 is out of sequence (expected 5) : FEC algorithm reseted !
        >>> g.put_media(R.create(2, 200, R.MP2T_PT, bytearray('Kuota Kharma Evo', 'utf-8')))
        Media seq=2 is out of sequence (expected 3) : FEC algorithm reseted !
        >>> print(g)
        Matrix size L x D            = 4 x 5
        Total invalid media packets  = 0
        Total media packets received = 5
        Column sequence number       = 1
        Row    sequence number       = 1
        Media  sequence number       = 3
        Medias buffer (seq. numbers) = [2]
        >>> if isinstance(g._medias[0].payload, bytearray):
        ...     assert g._medias[0].payload == bytearray('Kuota Kharma Evo', 'utf-8')
        ... else:
        ...     assert g._medias[0].payload == 'Kuota Kharma Evo'

        Testing a complete 3x4 matrix:

        >>> g = FecGenerator(3, 4)
        >>> R = RtpPacket
        >>> g.put_media(R.create(1, 100, R.MP2T_PT, bytearray('Tabby', 'utf-8')))
        Media seq=1 is out of sequence (expected None) : FEC algorithm reseted !
        >>> g.put_media(R.create(2, 200, R.MP2T_PT, bytearray('1234', 'utf-8')))
        >>> g.put_media(R.create(3, 300, R.MP2T_PT, bytearray('abcd', 'utf-8')))
        New ROW FEC packet seq=1 snbase=1 LxD=3xNone trec=384
        >>> g.put_media(R.create(4, 400, R.MP2T_PT, bytearray('python', 'utf-8')))
        >>> g.put_media(R.create(5, 500, R.MP2T_PT, bytearray('Kuota harma Evo', 'utf-8')))
        >>> g.put_media(R.create(6, 600, R.MP2T_PT, bytearray('h0ffman', 'utf-8')))
        New ROW FEC packet seq=2 snbase=4 LxD=3xNone trec=572
        >>> g.put_media(R.create(7, 700, R.MP2T_PT, bytearray('mutable', 'utf-8')))
        >>> g.put_media(R.create(8, 800, R.MP2T_PT, bytearray('10061987', 'utf-8')))
        >>> g.put_media(R.create(9, 900, R.MP2T_PT, bytearray('OSCIED', 'utf-8')))
        New ROW FEC packet seq=3 snbase=7 LxD=3xNone trec=536
        >>> g.put_media(R.create(10, 1000, R.MP2T_PT, bytearray('5ème élément', 'utf-8')))
        New COL FEC packet seq=1 snbase=1 LxD=3x4 trec=160
        >>> print(g)
        Matrix size L x D            = 3 x 4
        Total invalid media packets  = 0
        Total media packets received = 10
        Column sequence number       = 2
        Row    sequence number       = 4
        Media  sequence number       = 11
        Medias buffer (seq. numbers) = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> g.put_media(R.create(11, 1100, R.MP2T_PT, bytearray('Chaos Theory', 'utf-8')))
        New COL FEC packet seq=2 snbase=2 LxD=3x4 trec=1616
        >>> g.put_media(R.create(12, 1200, R.MP2T_PT, bytearray('Yes, it WORKS !', 'utf-8')))
        New ROW FEC packet seq=4 snbase=10 LxD=3xNone trec=788
        New COL FEC packet seq=3 snbase=3 LxD=3x4 trec=1088
        >>> print(g)
        Matrix size L x D            = 3 x 4
        Total invalid media packets  = 0
        Total media packets received = 12
        Column sequence number       = 4
        Row    sequence number       = 5
        Media  sequence number       = 13
        Medias buffer (seq. numbers) = []
        """
        self._total += 1
        if not media.valid:
            self._invalid += 1
            return

        # Compute expected media sequence number for next packet
        sequence = (media.sequence + 1) & RtpPacket.S_MASK

        # Ensure that protected media packets are not out of sequence to generate valid FEC
        # packets. If media packet sequence number is not at attended value, it may mean :
        # - Looped VLC broadcast session restarted media
        # - Some media packet are really lost between the emitter and this software
        # - An unknown feature (aka bug) makes this beautiful tool crazy !
        if self._media_sequence is not None and media.sequence == self._media_sequence:
            self._medias.append(media)
        else:
            self._medias = [media]
            self.on_reset(media)
        self._media_sequence = sequence

        # Compute a new row FEC packet when a new row just filled with packets
        if len(self._medias) % self._L == 0:
            row_medias = self._medias[-self._L:]
            assert len(row_medias) == self._L
            row = FecPacket.compute(
                self._row_sequence,
                FecPacket.XOR,
                FecPacket.ROW,
                self._L,
                self._D,
                row_medias)
            self._row_sequence = (self._row_sequence + 1) & RtpPacket.S_MASK
            self.on_new_row(row)

        # Compute a new column FEC packet when a new column just filled with packets
        if len(self._medias) > self._L * (self._D - 1):
            first = len(self._medias) - self._L * (self._D - 1) - 1
            col_medias = self._medias[first::self._L]
            assert len(col_medias) == self._D
            col = FecPacket.compute(
                self._col_sequence,
                FecPacket.XOR,
                FecPacket.COL,
                self._L,
                self._D,
                col_medias)
            self._col_sequence = (self._col_sequence + 1) & RtpPacket.S_MASK
            self.on_new_col(col)

        if len(self._medias) == self._L * self._D:
            self._medias = []

    def __str__(self):
        """
        Returns a string containing a formated representation of the FEC streams generator.

        **Example usage**

        >>> print(FecGenerator(5, 6))
        Matrix size L x D            = 5 x 6
        Total invalid media packets  = 0
        Total media packets received = 0
        Column sequence number       = 1
        Row    sequence number       = 1
        Media  sequence number       = None
        Medias buffer (seq. numbers) = []
        """
        medias = [p.sequence for p in self._medias]
        return f"""Matrix size L x D            = {self._L} x {self._D}
Total invalid media packets  = {self._invalid}
Total media packets received = {self._total}
Column sequence number       = {self._col_sequence}
Row    sequence number       = {self._row_sequence}
Media  sequence number       = {self._media_sequence}
Medias buffer (seq. numbers) = {medias}"""
