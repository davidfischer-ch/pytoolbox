# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                   OPTIMIZED AND CROSS PLATFORM SMPTE 2022-1 FEC LIBRARY IN C, JAVA, PYTHON, +TESTBENCH
#
#  Description    : SMPTE 2022-1 FEC Library
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2008-2013 smpte2022lib Team. All rights reserved.
#  Sponsoring     : Developed for a HES-SO CTI Ra&D project called GaVi
#                   Haute école du paysage, d'ingénierie et d'architecture @ Genève
#                   Telecommunications Laboratory
#
#**********************************************************************************************************************#
#
# This file is part of smpte2022lib.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/smpte2022lib.git

from __future__ import absolute_import

from ..rtp import RtpPacket
from .base import FecPacket


class FecGenerator(object):
    u"""
    A SMPTE 2022-1 FEC streams generator.
    This generator accept incoming RTP media packets and compute corresponding FEC packets.
    """

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Properties >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    @property
    def L(self):
        u"""
        Returns the Horizontal size of the FEC matrix (columns).

        **Example usage**

        >>> print FecGenerator(4, 5).L
        4
        """
        return self._L

    @property
    def D(self):
        u"""
        Returns the vertical size of the FEC matrix (rows).

        **Example usage**

        >>> print FecGenerator(4, 5).D
        5
        """
        return self._D

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Constructor >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def __init__(self, L, D):
        u"""
        Construct a FecGenerator.

        :param L: Horizontal size of the FEC matrix (columns)
        :type L: int
        :param D: Vertical size of the FEC matrix (rows)
        :type D: int
        :param extra: Extra argument for ``on_new_col`` and ``on_new_row`` methods
        :type extra: object
        """
        self._L, self._D = L, D
        self._col_sequence = self._row_sequence = 1
        self._media_sequence = None
        self._medias = []
        self._invalid = self._total = 0

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Functions >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def on_new_col(self, col, caller):
        u"""
        Called by FecGenerator when a new column FEC packet is generated and available for output.

        By default this method only print a message to stdout.

        .. seealso::

            You can `monkey patch <http://stackoverflow.com/questions/5626193/what-is-monkey-patching>`_ it.

        :param col: Generated column FEC packet
        :type col: FecPacket
        :param caller: The generator that fired this method / event
        :type caller: FecGenerator
        """
        print(u'New COL FEC packet seq={0} snbase={1} LxD={2}x{3} trec={4}'.format(
              col.sequence, col.snbase, col.L, col.D, col.timestamp_recovery))

    def on_new_row(self, row, caller):
        u"""
        Called by FecGenerator when a new row FEC packet is generated and available for output.

        By default this method only print a message to stdout.

        .. seealso::

            You can `monkey patch <http://stackoverflow.com/questions/5626193/what-is-monkey-patching>`_ it.

        :param row: Generated row FEC packet
        :type row: FecPacket
        :param caller: The generator that fired this method / event
        :type caller: FecGenerator
        """
        print(u'New ROW FEC packet seq={0} snbase={1} LxD={2}x{3} trec={4}'.format(
              row.sequence, row.snbase, row.L, row.D, row.timestamp_recovery))

    def on_reset(self, media, caller):
        u"""
        Called by FecGenerator when the algorithm is resetted (an incoming media is out of sequence).

        By default this method only print a message to stdout.

        .. seealso::

            You can `monkey patch <http://stackoverflow.com/questions/5626193/what-is-monkey-patching>`_ it.

        :param media: Out of sequence media packet
        :type row: RtpPacket
        :param caller: The generator that fired this method / event
        :type caller: FecGenerator
        """
        print(u'Media seq={0} is out of sequence (expected {1}) : FEC algorithm resetted !'.format(
              media.sequence, self._media_sequence))

    def put_media(self, media):
        u"""
        Put an incoming media packet.

        :param media: Incoming media packet
        :type media: RtpPacket

        **Example usage**

        Testing input of out of sequence medias:

        >>> from nose.tools import assert_equal
        >>> g = FecGenerator(4, 5)
        >>> g.put_media(RtpPacket.create(1, 100, RtpPacket.MP2T_PT, bytearray(u'Tabby', u'utf-8')))
        Media seq=1 is out of sequence (expected None) : FEC algorithm resetted !
        >>> g.put_media(RtpPacket.create(1, 100, RtpPacket.MP2T_PT, bytearray(u'1234', u'utf-8')))
        Media seq=1 is out of sequence (expected 2) : FEC algorithm resetted !
        >>> g.put_media(RtpPacket.create(4, 400, RtpPacket.MP2T_PT, bytearray(u'abcd', u'utf-8')))
        Media seq=4 is out of sequence (expected 2) : FEC algorithm resetted !
        >>> g.put_media(RtpPacket.create(2, 200, RtpPacket.MP2T_PT, bytearray(u'python', u'utf-8')))
        Media seq=2 is out of sequence (expected 5) : FEC algorithm resetted !
        >>> g.put_media(RtpPacket.create(2, 200, RtpPacket.MP2T_PT, bytearray(u'Kuota Kharma Evo', u'utf-8')))
        Media seq=2 is out of sequence (expected 3) : FEC algorithm resetted !
        >>> print g
        Matrix size L x D            = 4 x 5
        Total invalid media packets  = 0
        Total media packets received = 5
        Column sequence number       = 1
        Row    sequence number       = 1
        Media  sequence number       = 3
        Medias buffer (seq. numbers) = [2]
        >>> if isinstance(g._medias[0].payload, bytearray):
        ...     assert_equal(g._medias[0].payload, bytearray(u'Kuota Kharma Evo', u'utf-8'))
        ... else:
        ...     assert_equal(g._medias[0].payload, u'Kuota Kharma Evo')

        Testing a complete 3x4 matrix:

        >>> g = FecGenerator(3, 4)
        >>> g.put_media(RtpPacket.create(1, 100, RtpPacket.MP2T_PT, bytearray(u'Tabby', u'utf-8')))
        Media seq=1 is out of sequence (expected None) : FEC algorithm resetted !
        >>> g.put_media(RtpPacket.create(2, 200, RtpPacket.MP2T_PT, bytearray(u'1234', u'utf-8')))
        >>> g.put_media(RtpPacket.create(3, 300, RtpPacket.MP2T_PT, bytearray(u'abcd', u'utf-8')))
        New ROW FEC packet seq=1 snbase=1 LxD=3xNone trec=384
        >>> g.put_media(RtpPacket.create(4, 400, RtpPacket.MP2T_PT, bytearray(u'python', u'utf-8')))
        >>> g.put_media(RtpPacket.create(5, 500, RtpPacket.MP2T_PT, bytearray(u'Kuota harma Evo', u'utf-8')))
        >>> g.put_media(RtpPacket.create(6, 600, RtpPacket.MP2T_PT, bytearray(u'h0ffman', u'utf-8')))
        New ROW FEC packet seq=2 snbase=4 LxD=3xNone trec=572
        >>> g.put_media(RtpPacket.create(7, 700, RtpPacket.MP2T_PT, bytearray(u'mutable', u'utf-8')))
        >>> g.put_media(RtpPacket.create(8, 800, RtpPacket.MP2T_PT, bytearray(u'10061987', u'utf-8')))
        >>> g.put_media(RtpPacket.create(9, 900, RtpPacket.MP2T_PT, bytearray(u'OSCIED', u'utf-8')))
        New ROW FEC packet seq=3 snbase=7 LxD=3xNone trec=536
        >>> g.put_media(RtpPacket.create(10, 1000, RtpPacket.MP2T_PT, bytearray(u'5ème élément', u'utf-8')))
        New COL FEC packet seq=1 snbase=1 LxD=3x4 trec=160
        >>> print g
        Matrix size L x D            = 3 x 4
        Total invalid media packets  = 0
        Total media packets received = 10
        Column sequence number       = 2
        Row    sequence number       = 4
        Media  sequence number       = 11
        Medias buffer (seq. numbers) = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> g.put_media(RtpPacket.create(11, 1100, RtpPacket.MP2T_PT, bytearray(u'Chaos Theory', u'utf-8')))
        New COL FEC packet seq=2 snbase=2 LxD=3x4 trec=1616
        >>> g.put_media(RtpPacket.create(12, 1200, RtpPacket.MP2T_PT, bytearray(u'Yes, it WORKS !', u'utf-8')))
        New ROW FEC packet seq=4 snbase=10 LxD=3xNone trec=788
        New COL FEC packet seq=3 snbase=3 LxD=3x4 trec=1088
        >>> print g
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
        if self._media_sequence and media.sequence == self._media_sequence:
            self._medias.append(media)
        else:
            self._medias = [media]
            self.on_reset(media, self)
        self._media_sequence = sequence
        # Compute a new row FEC packet when a new row just filled with packets
        if len(self._medias) % self._L == 0:
            row_medias = self._medias[-self._L:]
            assert(len(row_medias) == self._L)
            row = FecPacket.compute(self._row_sequence, FecPacket.XOR, FecPacket.ROW, self._L, self._D, row_medias)
            self._row_sequence = (self._row_sequence + 1) % RtpPacket.S_MASK
            self.on_new_row(row, self)
        # Compute a new column FEC packet when a new column just filled with packets
        if len(self._medias) > self._L * (self._D - 1):
            first = len(self._medias) - self._L * (self._D - 1) - 1
            col_medias = self._medias[first::self._L]
            assert(len(col_medias) == self._D)
            col = FecPacket.compute(self._col_sequence, FecPacket.XOR, FecPacket.COL, self._L, self._D, col_medias)
            self._col_sequence = (self._col_sequence + 1) % RtpPacket.S_MASK
            self.on_new_col(col, self)
        if len(self._medias) == self._L * self._D:
            self._medias = []

    def __str__(self):
        u"""
        Returns a string containing a formated representation of the FEC streams generator.

        **Example usage**

        >>> print FecGenerator(5, 6)
        Matrix size L x D            = 5 x 6
        Total invalid media packets  = 0
        Total media packets received = 0
        Column sequence number       = 1
        Row    sequence number       = 1
        Media  sequence number       = None
        Medias buffer (seq. numbers) = []
        """
        medias = [p.sequence for p in self._medias]
        return (u"""Matrix size L x D            = {0} x {1}
Total invalid media packets  = {2}
Total media packets received = {3}
Column sequence number       = {4}
Row    sequence number       = {5}
Media  sequence number       = {6}
Medias buffer (seq. numbers) = {7}""".format(self._L, self._D, self._invalid, self._total, self._col_sequence,
                                             self._row_sequence, self._media_sequence, medias))
