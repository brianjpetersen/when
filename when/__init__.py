# standard libraries
import os
# third party libraries
pass
# first party libraries
from . import (when, timezones, )


__where__ = os.path.dirname(os.path.abspath(__file__))


with open(os.path.join(__where__, '..', 'VERSION'), 'rb') as f:
    __version__ = f.read()


__all__ = ('__version__', '__where__', 'now', 'When', 'While', 'timezones')

When = when.When
While = when.While
now = when.now
timezones = timezones.timezones


__doc__ = When.__doc__
