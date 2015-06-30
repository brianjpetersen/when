# standard libraries
import os
# third party libraries
pass
# first party libraries
from . import (when, )


__all__ = ('__version__', 'now', 'is_timezone_aware', 'When', )

_where = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(_where, '..', 'VERSION'), 'rb') as f:
    __version__ = f.read()


When = when.When
now = when.now
is_timezone_aware = when.is_timezone_aware