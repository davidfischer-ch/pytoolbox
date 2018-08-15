# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import uuid, tempfile

from celery import states
from celery.result import AsyncResult
from passlib.hash import pbkdf2_sha512
from passlib.utils import consteq

from . import module
from .encoding import text_type, to_bytes, to_unicode
from .serialization import JsoneableObject
from .subprocess import cmd
from .validation import valid_email, valid_secret, valid_uuid

_all = module.All(globals())


class Model(JsoneableObject):
    """
    A base model using an UUID string has id.
    Maybe useful for the developers that use pyMongo driver directly w/o any ODM mapper.

    .. seealso::

        See the project called `OSCIED <https://github.com/ebu/OSCIED/blob/master/library/oscied_lib/models.py>`.
    """

    def __init__(self, _id=None):
        self._id = _id or text_type(uuid.uuid4())

    def is_valid(self, raise_exception):
        if not valid_uuid(self._id, none_allowed=False):
            self._E(raise_exception, '_id is not a valid uuid string')
        return True

    def _E(self, raise_exception, message):
        if raise_exception:
            raise TypeError(to_bytes('{0} : {1}'.format(self.__class__.__name__, message)))
        return False


class TaskModel(Model):
    """
    A base model storing some statistics and the status of a celery task.
    Maybe useful for the developers that use pyMongo driver directly w/o any ODM mapper.

    .. seealso::

        See the project called `OSCIED <https://github.com/ebu/OSCIED/blob/master/library/oscied_lib/models.py>`.
    """

    ALL_STATUS = (
        PENDING, RECEIVED, STARTED, PROGRESS, SUCCESS,
        FAILURE, REVOKING, REVOKED, RETRY, IGNORED,
        UNKNOWN
    ) = (
        states.PENDING, states.RECEIVED, states.STARTED, 'PROGRESS', states.SUCCESS,
        states.FAILURE, 'REVOKING', states.REVOKED, states.RETRY, states.IGNORED,
        'UNKNOWN'
    )

    PENDING_STATUS = (PENDING, RECEIVED)
    RUNNING_STATUS = (STARTED, PROGRESS, RETRY)
    SUCCESS_STATUS = (SUCCESS, )
    CANCELED_STATUS = (REVOKING, REVOKED)
    ERROR_STATUS = (FAILURE, )
    UNDEF_STATUS = (IGNORED, UNKNOWN)
    FINAL_STATUS = SUCCESS_STATUS + CANCELED_STATUS + ERROR_STATUS
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
            return AsyncResult(self._id).result['hostname']
        except:
            return None

    def append_async_result(self):
        async_result = AsyncResult(self._id)
        if async_result:
            try:
                if self.status not in TaskModel.CANCELED_STATUS:
                    self.status = async_result.status
                try:
                    self.statistic.update(async_result.result)
                except:
                    self.statistic['error'] = to_unicode(async_result.result)
            except NotImplementedError:
                self.status = TaskModel.UNKNOWN
        else:
            self.status = TaskModel.UNKNOWN


class User(Model):
    """Example User model inherited from Model.

    .. seealso::

        See the project called `OSCIED <https://github.com/ebu/OSCIED/blob/master/library/oscied_lib/models.py>`.
    """

    def __init__(self, first_name=None, last_name=None, mail=None, secret=None,
                 admin_platform=False, _id=None):
        super(User, self).__init__(_id)
        self.first_name = first_name
        self.last_name = last_name
        self.mail = mail
        self.secret = secret
        self.admin_platform = (to_unicode(admin_platform).lower() == 'true')

    @property
    def credentials(self):
        return (self.mail, self.secret)

    @property
    def name(self):
        if self.first_name and self.last_name:
            return '{0} {1}'.format(self.first_name, self.last_name)
        return 'anonymous'

    @property
    def is_secret_hashed(self):
        return self.secret is not None and self.secret.startswith('$pbkdf2-sha512$')

    def is_valid(self, raise_exception):
        if not super(User, self).is_valid(raise_exception):
            return False
        # FIXME check first_name
        # FIXME check last_name
        if not valid_email(self.mail):
            self._E(raise_exception, 'mail is not a valid email address')
        if not self.is_secret_hashed and not valid_secret(self.secret, True):
            self._E(raise_exception,
                    'secret is not safe (8+ characters, upper/lower + numbers eg. StrongP6s)')
        # FIXME check admin_platform
        return True

    def hash_secret(self, rounds=12000, salt=None, salt_size=16):
        """
        Hashes user's secret if it is not already hashed.

        **Example usage**

        >>> user = User(first_name='D.', last_name='F.', mail='d@f.com', secret='Secr4taB', admin_platform=True)
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
        """
        Returns True if secret is equal to user's secret.

        **Example usage**

        >>> user = User(first_name='D.', last_name='F.', mail='d@f.com', secret='Secr4taB', admin_platform=True)
        >>> user.verify_secret('bad_secret')
        False
        >>> user.verify_secret('Secr4taB')
        True
        >>> user.hash_secret()
        >>> user.verify_secret('bad_secret')
        False
        >>> user.verify_secret('Secr4taB')
        True
        """
        if self.is_secret_hashed:
            return pbkdf2_sha512.verify(secret, self.secret)
        return consteq(secret, self.secret)


def mongo_do(action, database=None, fail=True, log=None, **kwargs):
    action_file = tempfile.NamedTemporaryFile(mode='w', suffix='.js')
    action_file.write(action)
    try:
        return cmd(
            filter(None, ['mongo', database, action_file.name]), fail=fail, log=log, **kwargs)
    finally:
        action_file.close()


__all__ = _all.diff(globals())
