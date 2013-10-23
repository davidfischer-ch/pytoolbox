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

from __future__ import absolute_import, division, print_function, unicode_literals

import logging, sys


def setup_logging(name=u'', reset=False, filename=None, console=False, level=logging.DEBUG,
                  fmt=u'%(asctime)s %(levelname)-8s - %(message)s', datefmt=u'%d/%m/%Y %H:%M:%S'):
    u"""
    Setup logging (TODO).

    :param name: TODO
    :type name: str
    :param reset: Unregister all previously registered handlers ?
    :type reset: bool
    :param filename: TODO
    :type name: str
    :param console: Toggle console output (stdout)
    :type console: bool
    :param level: TODO
    :type level: int
    :param fmt: TODO
    :type fmt: str
    :param datefmt: TODO
    :type datefmt: str

    **Example usage**

    Setup a console output for logger with name *test*:

    >>> setup_logging(name=u'test', reset=True, console=True, fmt=None, datefmt=None)
    >>> log = logging.getLogger(u'test')
    >>> log.info(u'this is my info')
    this is my info
    >>> log.debug(u'this is my debug')
    this is my debug
    >>> log.setLevel(logging.INFO)
    >>> log.debug(u'this is my hidden debug')
    >>> log.handlers = []  # Remove handlers manually: pas de bras, pas de chocolat !
    >>> log.debug(u'no handlers, no messages ;-)')

    Show how to reset handlers of the logger to avoid duplicated messages (e.g. in doctest):

    >>> setup_logging(name=u'test', console=True, fmt=None, datefmt=None)
    >>> setup_logging(name=u'test', console=True, fmt=None, datefmt=None)
    >>> log.info(u'double message, tu radote pépé')
    double message, tu radote pépé
    double message, tu radote pépé
    >>> setup_logging(name=u'test', reset=True, console=True, fmt=None, datefmt=None)
    >>> log.info(u'single message')
    single message
    """
    if reset:
        logging.getLogger(name).handlers = []
    if filename:
        log = logging.getLogger(name)
        log.setLevel(level)
        handler = logging.FileHandler(filename)
        handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        log.addHandler(handler)
    if console:
        log = logging.getLogger(name)
        log.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        log.addHandler(handler)
