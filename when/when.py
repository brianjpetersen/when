# standard libraries
import datetime
import time
# third party libraries
import collections
import dateutil
import pytz
# first party libraries
pass


class While:
    """ A friendly alternative to ```datetime.timedelta``` with intuitive attributes.

    """

    def __init__(self, years=0, months=0, days=0, hours=0, minutes=0, 
                 seconds=0, milliseconds=0, microseconds=0):
        pass

    @classmethod
    def from_timedelta(cls, timedelta):
        pass

    def shift(self, years=0, ):
        pass

    def humanize(self):
        pass

    def __add__(self, other):
        pass

    def __sub__(self, other):
        pass

    def __div__(self, other):
        pass

    def __mul__(self, other):
        pass


class When(datetime.datetime):
    """ Python dates and times for humans.

        >>> d = When.from_datetime(datetime.datetime.utcnow(), )
        >>> 

    """

    def __new__(cls, year, month, day=None, hour=0, minute=0, 
                second=0, millisecond=0, microsecond=0, timezone=pytz.utc):
        _microsecond = 1000*millisecond + microsecond
        naive = datetime.datetime.__new__(cls, year, month, day, hour, minute, 
                                          second, _microsecond)

        return 


    @classmethod
    def from_datetime(cls, datetime, timezone=None, dst=False):
        return cls(datetime.year, datetime.month, datetime.day, datetime.hour,
                   datetime.minute, datetime.second, datetime.microsecond, 
                   datetime.tzinfo)

    @classmethod
    def from_iso8601(cls, iso8601, timezone=None):
        pass

    @classmethod
    def from_timestamp(cls, ):
        pass

    @classmethod
    def now(cls, timezone=pytz.utc, dst=False):
        now = datetime.datetime.utcnow()
        when = cls(now.year, now.month, now.day, now.hour, now.minute, 
                   now.second, now.microsecond, pytz.utc)
        return when.to(timezone)

    def to(self, timezone):
        pytz.timezone(timezone)

    def replace(self):
        pass

    def __format__(self, specifier):
        pass

    def __add__(self, other):
        pass

    def __sub__(self, other):
        pass

    def _get_timezone(self):
        return self.tzinfo
    timezone = property(_get_timezone)

    def _get_datetime(self):
        return datetime.datetime(self.year, self.month, self.day, self.hour, self.minute, 
                                 self.second, self.microsecond, tzinfo=self.tzinfo)
    datetime = property(_get_datetime)

    def _get_date(self):
        return datetime.datetime.date(self)
    date = property(_get_date)


def now(timezone=pytz.utc, dst=False):
    return When.now(timezone, dst)


def parse(*args, **kwargs):
    raise dateutil.parser.parse(*args)

def sleep(seconds):
    time.sleep(seconds)

"""
Jan
January 30, 1984 1:30 pm
"""