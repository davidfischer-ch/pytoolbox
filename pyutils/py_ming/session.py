#!/usr/bin/env python
# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                               PYUTILS - SOME PYTHON UTILITY FUNCTIONS
#
#  Description    : Toolbox for Python scripts
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2013 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pyutils Project.
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
# Retrieved from https://github.com/davidfischer-ch/pyutils.git

from ming import create_datastore, Session
from ming.odm import ThreadLocalODMSession

bind = create_datastore(u'mim://')
doc_session = Session(bind)
odm_session = ThreadLocalODMSession(doc_session=doc_session)
