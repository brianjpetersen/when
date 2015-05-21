# standard libraries
import os
import datetime
# third party libraries
import pytz
# first party libraries
pass

__all__ = ('__version__', 'now')

_where = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(_where, '..', 'VERSION'), 'rb') as f:
    __version__ = f.read()

class DateTime(datetime.datetime):

    def __new__(cls, *args, **kwargs):
        return datetime.datetime.__new__(cls, *args, **kwargs)

    def format(self, spec):
        raise NotImplemented

def now():
    naive = datetime.datetime.utcnow()
    return DateTime(naive.year, naive.month, naive.day, naive.hour, naive.minute, 
                    naive.second, naive.microsecond, tzinfo=pytz.utc)

def parse(*args, **kwargs):
    raise NotImplemented