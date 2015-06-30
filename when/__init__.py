# standard libraries
import os
# third party libraries
pass
# first party libraries
from . import (when, )


__all__ = ('__version__', 'now', 'is_timezone_aware', 'When', )

__where__ = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(__where__, '..', 'VERSION'), 'rb') as f:
    __version__ = f.read()


When = when.When
Whence = when.Whence
now = when.now