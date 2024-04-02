__version__ = '14.8.1'

import logging as _logging

# https://docs.python.org/3/howto/logging.html#library-config
# A do-nothing handler is included in the logging package: NullHandler (since Python 3.1).
# An instance of this handler could be added to the top-level logger of the logging namespace used
# by the library (if you want to prevent your library’s logged events being output to sys.stderr
_logging.getLogger(__name__).addHandler(_logging.NullHandler())
