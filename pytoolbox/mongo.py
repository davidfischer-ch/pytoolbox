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

import uuid
from celery import states
from celery.result import AsyncResult
from passlib.hash import pbkdf2_sha512
from passlib.utils import consteq
from .encoding import to_bytes
from .serialization import JsoneableObject
from .validation import valid_email, valid_secret, valid_uuid


class Model(JsoneableObject):
    u"""
    A base model using an UUID string has id.
    Maybe useful for the developers that use pyMongo driver directly w/o any ODM mapper.

    .. seealso::

        See the project called `OSCIED <https://github.com/ebu/OSCIED/blob/master/library/oscied_lib/models.py>`.
    """

    def __init__(self, _id=None):
        self._id = _id or unicode(uuid.uuid4())

    def is_valid(self, raise_exception):
        if not valid_uuid(self._id, none_allowed=False):
            self._E(raise_exception, u'_id is not a valid uuid string')
        return True

    def _E(self, raise_exception, message):
        if raise_exception:
            raise TypeError(to_bytes(u'{0} : {1}'.format(self.__class__.__name__, message)))
        return False


class TaskModel(Model):
    u"""
    A base model storing some statistics and the status of a celery task.
    Maybe useful for the developers that use pyMongo driver directly w/o any ODM mapper.

    .. seealso::

        See the project called `OSCIED <https://github.com/ebu/OSCIED/blob/master/library/oscied_lib/models.py>`.
    """

    ALL_STATUS = PENDING, RECEIVED, STARTED, PROGRESS, SUCCESS, FAILURE, REVOKING, REVOKED, RETRY, IGNORED, UNKNOWN = \
        states.PENDING, states.RECEIVED, states.STARTED, u'PROGRESS', states.SUCCESS, states.FAILURE, u'REVOKING', \
        states.REVOKED, states.RETRY, states.IGNORED, u'UNKNOWN'

    PENDING_STATUS  = (PENDING, RECEIVED)
    RUNNING_STATUS  = (STARTED, PROGRESS, RETRY)
    SUCCESS_STATUS  = (SUCCESS, )
    CANCELED_STATUS = (REVOKING, REVOKED)
    ERROR_STATUS    = (FAILURE, )
    UNDEF_STATUS    = (IGNORED, UNKNOWN)
    FINAL_STATUS    = SUCCESS_STATUS + CANCELED_STATUS + ERROR_STATUS
    WORK_IN_PROGRESS_STATUS = PENDING_STATUS + RUNNING_STATUS

    def __init__(self, _id=None, statistic=None, status=UNKNOWN):
        super(TaskModel, self).__init__(_id)
        self.statistic = statistic or {}
        self.status = status

    def is_valid(self, raise_exception):
        if not super(TaskModel, self).is_valid(raise_exception):
            return False
        # FIXME check statistic
        # FIXME check status
        return True

    def get_hostname(self):
        try:
            return AsyncResult(self._id).result[u'hostname']
        except:
            return None

    def append_async_result(self):
        async_result = AsyncResult(self._id)
        if async_result:
            try:
                if self.status not in (TaskModel.REVOKED, TaskModel.REVOKING):
                    self.status = async_result.status
                try:
                    self.statistic.update(async_result.result)
                except:
                    self.statistic[u'error'] = unicode(async_result.result)
            except NotImplementedError:
                self.status = TaskModel.UNKNOWN
        else:
            self.status = TaskModel.UNKNOWN


class User(Model):
    u"""Example User model inherited from Model.

    .. seealso::

        See the project called `OSCIED <https://github.com/ebu/OSCIED/blob/master/library/oscied_lib/models.py>`.
    """

    def __init__(self, first_name=None, last_name=None, mail=None, secret=None, admin_platform=False, _id=None):
        super(User, self).__init__(_id)
        self.first_name = first_name
        self.last_name = last_name
        self.mail = mail
        self.secret = secret
        self.admin_platform = (unicode(admin_platform).lower() == u'true')

    @property
    def credentials(self):
        return (self.mail, self.secret)

    @property
    def name(self):
        if self.first_name and self.last_name:
            return u'{0} {1}'.format(self.first_name, self.last_name)
        return u'anonymous'

    @property
    def is_secret_hashed(self):
        return self.secret is not None and self.secret.startswith(u'$pbkdf2-sha512$')

    def is_valid(self, raise_exception):
        if not super(User, self).is_valid(raise_exception):
            return False
        # FIXME check first_name
        # FIXME check last_name
        if not valid_email(self.mail):
            self._E(raise_exception, u'mail is not a valid email address')
        if not self.is_secret_hashed and not valid_secret(self.secret, True):
            self._E(raise_exception, u'secret is not safe (8+ characters, upper/lower + numbers eg. StrongP6s)')
        # FIXME check admin_platform
        return True

    def hash_secret(self, rounds=12000, salt=None, salt_size=16):
        u"""
        Hashes user's secret if it is not already hashed.

        **Example usage**

        >>> user = User(first_name=u'D.', last_name=u'F.', mail=u'd@f.com', secret=u'Secr4taB', admin_platform=True)
        >>> user.is_secret_hashed
        False
        >>> len(user.secret)
        8
        >>> user.hash_secret()
        >>> user.is_secret_hashed
        True
        >>> len(user.secret)
        130
        >>> secret = user.secret
        >>> user.hash_secret()
        >>> assert(user.secret == secret)
        """
        if not self.is_secret_hashed:
            self.secret = pbkdf2_sha512.encrypt(
                self.secret, rounds=rounds, salt=salt, salt_size=salt_size)

    def verify_secret(self, secret):
        u"""
        Returns True if secret is equal to user's secret.

        **Example usage**

        >>> user = User(first_name=u'D.', last_name=u'F.', mail='d@f.com', secret=u'Secr4taB', admin_platform=True)
        >>> user.verify_secret(u'bad_secret')
        False
        >>> user.verify_secret(u'Secr4taB')
        True
        >>> user.hash_secret()
        >>> user.verify_secret(u'bad_secret')
        False
        >>> user.verify_secret(u'Secr4taB')
        True
        """
        if self.is_secret_hashed:
            return pbkdf2_sha512.verify(secret, self.secret)
        return consteq(secret, self.secret)
