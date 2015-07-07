# standard libraries
import datetime
import time
import warnings
# third party libraries
import collections
import dateutil
import pytz
# first party libraries
from . import (timezones, )


timezones = timezones.timezones


class While:
    """ An alternative to ```datetime.timedelta``` with intuitive attributes.
        
    """

    def __init__(self, years=0, months=0, days=0, hours=0, minutes=0, 
                 seconds=0, milliseconds=0, microseconds=0):
        pass

    @classmethod
    def from_timedelta(cls, timedelta):
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
    
    def __abs__(self):
        pass


IMMUTABLE_ATTRS = set(('year', 'month', 'day', 'hour', 'minute', 'second', 
                       'microsecond'))


class When(datetime.datetime):
    """ Python dates and times for humans.
        
        >>> 
        >>> 
        
    """
    
    def __new__(cls, year, month, day, hour=0, minute=0, second=0, 
                microsecond=0, timezone='utc', dst=False):
        naive = datetime.datetime(year, month, day, hour, minute, 
                                  second, microsecond)
        local = timezones[timezone].localize(naive, dst)
        datetime_dict = cls.datetime_to_dict(local, tzinfo=True)
        return datetime.datetime.__new__(cls, **datetime_dict)
        
    def __init__(self, year, month, day, hour=0, minute=0, second=0, 
                 microsecond=0, timezone='utc', dst=False):
        self._timezone_string = timezone
        self.utc = None

    @staticmethod
    def datetime_to_dict(datetime, tzinfo=False):
        datetime_dict = {}
        attrs = ('year', 'month', 'day', 'hour', 'minute', 'second', 
                 'microsecond', 'tzinfo', )
        for attr in attrs:
            try:
                datetime_dict[attr] = getattr(datetime, attr)
            except AttributeError:
                continue
        if not tzinfo:
            del datetime_dict['tzinfo']
        return datetime_dict
        
    @classmethod
    def from_datetime(cls, datetime, timezone, dst=False):
        if datetime.tzinfo:
            warning = 'Note, this datetime is not naive, and the tzinfo {} \
                       associated with it is being ignored in \
                       favor of {}.'.format(str(datetime.tzinfo), timezone)
            warnings.warn(warning)
        datetime_dict = cls.datetime_to_dict(datetime, tzinfo=False)
        datetime_dict['timezone'] = timezone
        datetime_dict['dst'] = dst
        return cls(**datetime_dict)
        
    from_date = from_datetime
    
    @classmethod
    def now(cls, timezone='utc'):
        naive = datetime.datetime.utcnow()
        datetime_dict = cls.datetime_to_dict(naive, tzinfo=False)
        datetime_dict['timezone'] = 'utc'
        now = cls(**datetime_dict)
        now.timezone = timezone
        return now
    
    """
    def __getattr__(self, attr):
        print('in __getattr__', attr)
        if attr in IMMUTABLE_ATTRS:
            return getattr(self, '_' + attr)
        else:
            return self.__dict__[attr]
        
    def __setattr__(self, attr, val):
        print('in __setattr__', attr, val)
        if attr in IMMUTABLE_ATTRS:
            raise AttributeError('Attribute "{}" is immutable.  To modify \
                                  this attribute, use the ```replace``` \
                                  method.'.format(attr))
        elif attr == 'timezone':
            timezone = val
            local = self.astimezone(timezones[timezone])
            self._update_immutable_attrs_from_datetime(local)
        else:
            self.__dict__[attr] = val
    """
    
    def _get_hour(self):
        return self._hour
        
    def _set_hour(self, hour):
        raise AttributeError('Attribute "hour" is immutable.')
        
    hour = property(_get_hour, _set_hour)
    
    def _update_immutable_attrs_from_datetime(self, datetime):
        for attr in IMMUTABLE_ATTRS:
            setattr(self, '_' + attr, getattr(datetime, attr))
    
    def _get_timezone(self):
        return timezones[self._timezone_string]
    
    def _set_timezone(self, timezone):
        local = self.astimezone(timezones[timezone])
        self._update_immutable_attrs_from_datetime(local)
    
    timezone = property(_get_timezone, _set_timezone)


def now(timezone='utc'):
    return When.now(timezone)


def parse(*args, **kwargs):
    raise dateutil.parser.parse(*args)


def sleep(seconds):
    time.sleep(seconds)

"""
Jan
January 30, 1984 1:30 pm
"""