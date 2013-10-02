#!/usr/bin/env python
# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                                       PYUTILS - TOOLBOX FOR PYTHON SCRIPTS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pytoolbox Project.
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
# Retrieved from https://github.com/davidfischer-ch/pytoolbox.git

from __future__ import absolute_import, division

import logging, socket, struct, time
from ....encoding import to_bytes
from ...rtp import RtpPacket
from ..generator import FecGenerator

log = logging.getLogger(u'smpte2022lib')


# FIXME send to multicast address fail (?)
class SocketFecGenerator(object):
    u"""
    A SMPTE 2022-1 FEC streams generator with network skills based on :mod:`socket`.

    This generator listen to incoming RTP media stream, compute and output corresponding FEC streams.

    **Example usage**

    >>> from ...ip import IPSocket
    >>> media = IPSocket(SocketFecGenerator.DEFAULT_MEDIA)
    >>> col = IPSocket(SocketFecGenerator.DEFAULT_COL)
    >>> row = IPSocket(SocketFecGenerator.DEFAULT_ROW)
    >>> generator = SocketFecGenerator(media, col, row, 5, 6)
    >>> print(generator._generator)
    Matrix size L x D            = 5 x 6
    Total invalid media packets  = 0
    Total media packets received = 0
    Column sequence number       = 1
    Row    sequence number       = 1
    Media  sequence number       = None
    Medias buffer (seq. numbers) = []
    """

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Properties >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    DEFAULT_MEDIA = u'239.232.0.222:5004'
    DEFAULT_COL = u'232.232.0.222:5006'
    DEFAULT_ROW = u'232.232.0.222:5008'

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Constructor >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def __init__(self, media_socket, col_socket, row_socket, L, D):
        u"""
        Construct a SocketFecGenerator.

        :param media_socket: Socket of incoming RTP media stream
        :type media_socket: IPSocket
        :param col_socket: Socket of output FEC stream (column)
        :type col_socket: IPSocket
        :param row_socket: Socket of output FEC stream (row)
        :type row_socket: IPSocket
        :param L: Horizontal size of the FEC matrix (columns)
        :type L: int
        :param D: Vertical size of the FEC matrix (rows)
        :type D: int
        """
        self.media_socket = media_socket
        self.col_socket = col_socket
        self.row_socket = row_socket
        self._generator = FecGenerator(L, D)
        self._generator.on_new_col = self.on_new_col
        self._generator.on_new_row = self.on_new_row
        self._generator.on_reset = self.on_reset
        self._running = False

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Properties >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    @property
    def running(self):
        u"""Return True if FEC generator is running."""
        return self._running

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Functions >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def run(self, timeout, stop_time=None):
        u"""
        Run FEC generator main loop.

        .. note::

            * Raise an exception if called when FEC generator is already running.
            * If ``timeout`` is None then this method will uses blocking socket operations:
                -> Stop requests may be never taken into account !

        :param timeout: Set a timeout on blocking socket operations (in seconds, or None).
        :type timeout: float

        **Example usage**

        >> print('TODO lazy developer !')
        I've done the code, but not the example ... I will do it later ...
        """
        if self._running:
            raise NotImplementedError(to_bytes(u'SMPTE 2022-1 FEC Generator already running'))
        try:
            self._running = True
            log.info(u'SMPTE 2022-1 FEC Generator by David Fischer')
            log.info(u'Started listening {0}'.format(self.media_socket))
            if stop_time:
                timeout = timeout or 1.0  # Ensure a time-out to handle stop time
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            sock.bind((self.media_socket[u'ip'], self.media_socket[u'port']))
            # Tell the operating system to add the socket to the multicast group on all interfaces
            group = socket.inet_aton(self.media_socket[u'ip'])
            mreq = struct.pack('4sL', group, socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            sock.settimeout(timeout)  # Time-out must be enabled to react to stop requests
            while self._running:      # Receive loop
                try:
                    datagram, address = sock.recvfrom(1024)
                    media = RtpPacket(bytearray(datagram), len(datagram))
                    log.debug(u'Incoming media packet seq={0} ts={1} psize={2} ssrc={3} address={4}'.format(
                              media.sequence, media.timestamp, media.payload_size, media.ssrc, address))
                    self._generator.put_media(media)
                except socket.timeout:
                    pass  # Handle time-out by doing nothing more than re-looping
                delta_time = time.time() - start_time
                if stop_time and delta_time > stop_time:
                    break
            log.info(u'Stopped listening {0} after {1} seconds'.format(self.media_socket, delta_time))
        finally:
            self.stop()

    def stop(self):
        u"""
        Ask the FEC generator to stop.

        The request will be taken into account by generator's main loop.
        Polling interval correspond to ``run()`` ``timeout`` parameter.
        """
        log.info(u'\nGenerator stopped\n')
        self._running = False

    def on_new_col(self, col, generator):
        u"""
        Called by ``self=FecGenerator`` when a new column FEC packet is generated and available for output.

        Send the encapsulated column FEC packet.

        :param col: Generated column FEC packet
        :type col: FecPacket
        :param generator: The generator that fired this method / event
        :type generator: FecGenerator
        """
        col_rtp = RtpPacket.create(col.sequence, 0, RtpPacket.DYNAMIC_PT, col.bytes)
        log.debug(u'Send COL FEC packet seq={0} snbase={1} LxD={2}x{3} trec={4} socket={5}'.format(
                  col.sequence, col.snbase, col.L, col.D, col.timestamp_recovery, self.col_socket))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.sendto(col_rtp.bytes, (self.col_socket[u'ip'], self.col_socket[u'port']))

    def on_new_row(self, row, generator):
        u"""
        Called by ``self=FecGenerator`` when a new row FEC packet is generated and available for output.

        Send the encapsulated row FEC packet.

        :param row: Generated row FEC packet
        :type row: FecPacket
        :param generator: The generator that fired this method / event
        :type generator: FecGenerator
        """
        row_rtp = RtpPacket.create(row.sequence, 0, RtpPacket.DYNAMIC_PT, row.bytes)
        log.debug(u'Send ROW FEC packet seq={0} snbase={1} LxD={2}x{3} trec={4} socket={5}'.format(
                  row.sequence, row.snbase, row.L, row.D, row.timestamp_recovery, self.row_socket))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.sendto(row_rtp.bytes, (self.row_socket[u'ip'], self.row_socket[u'port']))

    def on_reset(self, media, generator):
        u"""
        Called by ``self=FecGenerator`` when the algorithm is resetted (an incoming media is out of sequence).

        Log a warning message.

        :param media: Out of sequence media packet
        :type row: RtpPacket
        :param generator: The generator that fired this method / event
        :type generator: FecGenerator
        """
        log.warning(u'Media seq={0} is out of sequence (expected {1}) : FEC algorithm resetted !'.format(
                    media.sequence, generator._media_sequence))


def main():
    u"""
    This is a working example utility using this class, this method will :

    * Parse arguments from command line
    * Register handlers to SIGTERM and SIGINT
    * Instantiate a :mod:`SocketFecGenerator` and start it
    """
    import doctest, errno, signal
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType
    from pytoolbox.encoding import configure_unicode
    from pytoolbox.logging import setup_logging
    from ...ip import IPSocket

    configure_unicode()
    setup_logging(name=u'smpte2022lib', filename=None, console=True, level=logging.DEBUG)
    log.info(u'Testing SocketFecGenerator with doctest')
    doctest.testmod(verbose=False)
    log.info(u'OK')

    HELP_MEDIA   = u'Socket of input stream'
    HELP_COL     = u'Socket of generated FEC column stream'
    HELP_ROW     = u'Socket of generated FEC row stream'
    HELP_L       = u'Horizontal size of the FEC matrix (columns)'
    HELP_D       = u'Vertical size of the FEC matrix (rows)'
    HELP_TIMEOUT = u'Set timeout for socket operations (in seconds)'
    HELP_PROFILE = u'Set profiling output file (this enable profiling)'
    HELP_STOP    = u'Automatic stop time (in seconds)'

    dmedia = SocketFecGenerator.DEFAULT_MEDIA
    dcol = SocketFecGenerator.DEFAULT_COL
    drow = SocketFecGenerator.DEFAULT_ROW

    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        epilog=u'''This utility create SMPTE 2022-1 FEC streams from a sniffed source stream.
                   SMPTE 2022-1 help streaming systems to improve QoE of real-time RTP transmissions.''')
    parser.add_argument(u'-m', u'--media',        type=IPSocket,      help=HELP_MEDIA,   default=dmedia)
    parser.add_argument(u'-c', u'--col',          type=IPSocket,      help=HELP_COL,     default=dcol)
    parser.add_argument(u'-r', u'--row',          type=IPSocket,      help=HELP_ROW,     default=drow)
    parser.add_argument(u'-l',                    type=int,           help=HELP_L,       default=5)
    parser.add_argument(u'-d',                    type=int,           help=HELP_D,       default=6)
    parser.add_argument(u'-t', u'--timeout',      type=int,           help=HELP_TIMEOUT, nargs='?', default=None)
    parser.add_argument(u'-s', u'--stop-time',    type=int,           help=HELP_STOP,    nargs='?', default=None)
    parser.add_argument(u'-p', u'--profile',      type=FileType('w'), help=HELP_PROFILE, nargs='?', default=None)
    args = parser.parse_args()

    def handle_stop_signal(SIGNAL, stack):
        generator.stop()

    try:
        signal.signal(signal.SIGTERM, handle_stop_signal)
        signal.signal(signal.SIGINT, handle_stop_signal)
        generator = SocketFecGenerator(args.media, args.col, args.row, args.l, args.d)
        if args.profile:
            from pycallgraph import PyCallGraph
            from pycallgraph.output import GraphvizOutput
            with PyCallGraph(output=GraphvizOutput(output_file=args.profile.name)):
                generator.run(args.timeout, args.stop_time)
        else:
            generator.run(args.timeout, args.stop_time)
    except socket.error as e:
        if e.errno != errno.EINTR:
            raise

if __name__ == u'__main__':
    main()
