# standard libraries
import os
# third party libraries
pass
# first party libraries
from . import (when, timezones, while_, during)


__where__ = os.path.dirname(os.path.abspath(__file__))


with open(os.path.join(__where__, '..', 'VERSION'), 'rb') as f:
    __version__ = f.read()


__all__ = ('__version__', '__where__', 'now', 'When', 'While', 'timezones',
           'tic', 'toc', 'sleep', 'Timer', )

When = when.When
While = while_.While
now = when.now
timezones = timezones.timezones
tic = during.tic
toc = during.toc
sleep = during.sleep
Timer = during.Timer


__doc__ = When.__doc__
