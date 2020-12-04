from selenium.common.exceptions import *  # noqa:F401,F403
from selenium.common.exceptions import NoSuchElementException


class NoSuchSpecializedElementException(NoSuchElementException):
    pass
