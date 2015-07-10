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


class When(datetime.datetime):
    """ Python dates and times for humans.
    
        The API for the standard library datetime module is broken.  Datetimes 
        are timezone-naive by default.  Datetime objects are entirely immutable,
        including timezones, even though 5p in New York is the *same* time as 
        2p in Los Angeles.  If my life depended on supplying a correct string 
        format specifier to strftime without consulting the documentation, 
        I'd start planning my funeral instead of even attempting.
        
        ```when.When``` addresses these issues, making dates and times more
        friendly and Pythonic.  Insomuch as possible, it maintains compatibility
        with the standard library datetime object (in both a duck-typing sense
        and an explicit ```isinstance```/```issubclass``` sense).
        
        >>> earth_day = When(year=2015, month=4, day=22, hour=5, 
        ...                  timezone='America/New_York')
        >>> print(earth_day)
        2015-04-22 05:00:00-04:00
        >>> earth_day.timezone = 'America/Los_Angeles'
        >>> print(earth_day)
        2015-04-22 02:00:00-07:00
        >>> earth_day.timezone
        <DstTzInfo 'America/Los_Angeles' LMT-1 day, 16:07:00 STD>
        >>> isinstance(earth_day, datetime.datetime)
        True
        >>> issubclass(When, datetime.datetime)
        True
        >>> earth_day.year, earth_day.day, earth_day.hour, earth_day.minute
        (2015, 22, 2, 0)
        >>> print(earth_day.utc)
        2015-04-22 09:00:00+00:00
        
        ```when.When``` is a thin wrapper over a Python datetime object and
        Pytz.  It proxies most attribute access to an underlying timezone-aware 
        datetime object, and modifies constructors to handle timezone-awareness 
        by default.  It is immutable in the sense that attributes cannot be 
        modified that would change the unique instant the object represents
        (put more technically, the UTC datetime is invariant), but timezones
        are mutable and are treated as views.
    """
    
    __immutables = set(('year', 'month', 'day', 'hour', 'minute', 'second', 
                        'microsecond'))
                        
    def __new__(cls, *args, **kwargs):
        """ We need to subclass from datetime.datetime to allow the following 
            two conditions to be met:
        
              1. issubclass(When, datetime.datetime) == True
              2. isinstance(When(), datetime.datetime) == True
        
            However, because we will actually be proxying most attribute access 
            to an underyling datetime object, it actually doesn't matter what 
            we return here, as long as it is subclassed from datetime.
        """
        return datetime.datetime.__new__(cls, 1111, 2, 3, 4, 5, 6, 777777)
    
    def __init__(self, year, month, day, hour=0, minute=0, second=0, 
                 microsecond=0, timezone='utc', dst=False):
        naive = datetime.datetime(year, month, day, hour, minute, 
                                  second, microsecond)
        self.__datetime = timezones[timezone].localize(naive, dst)
        self.__timezone = timezone
        
    @classmethod
    def from_datetime(cls, datetime, timezone, dst=False):
        """ Construct a When from a standard-library datetime and a timezone.
        
            Note, any naive tzinfo supplied as part of the datetime will be 
            ignored in favor of the ```timezone``` variable, and warning will 
            be issued.
            
            >>> d = datetime.datetime(2015, 1, 1)
            >>> When.from_datetime(d, 'utc')
            datetime.datetime(2015, 1, 1, 0, 0, tzinfo=<UTC>)
            >>> d = datetime.datetime(2015, 1, 1, tzinfo=timezones['America/New_York'])
            >>> warnings.filterwarnings('error')
            >>> When.from_datetime(d, 'utc')
            Traceback (most recent call last):
              File "/usr/lib/python3.4/doctest.py", line 1324, in __run
                compileflags, 1), test.globs)
              File "<doctest when.when.When.from_datetime[4]>", line 1, in <module>
                When.from_datetime(d, 'utc')
              File "/home/ubuntu/workspace/when/when/when.py", line 138, in from_datetime
                warnings.warn(warning)
            UserWarning: Note, this datetime is not naive, and the tzinfo America/New_York associated with it is being ignored in favor of the supplied timezone utc.
            >>> warnings.filterwarnings('ignore')
            >>> When.from_datetime(d, 'utc')
            datetime.datetime(2015, 1, 1, 0, 0, tzinfo=<UTC>)
            
        """
        if datetime.tzinfo:
            warning = ('Note, this datetime is not naive, and the tzinfo {} '
                       'associated with it is being ignored in '
                       'favor of the supplied '
                       'timezone {}.'.format(str(datetime.tzinfo), timezone))
            warnings.warn(warning)
        kwargs = cls.__extract_datetime_dict(datetime)
        kwargs['timezone'] = timezone
        kwargs['dst'] = dst
        return cls(**kwargs)
        
    @classmethod
    def __extract_datetime_dict(cls, datetime):
        datetime_dict = {}
        for attribute in cls.__immutables:
            try:
                datetime_dict[attribute] = getattr(datetime, attribute)
            except:
                continue
        return datetime_dict

    @property
    def utc(self):
        utc = getattr(self, '__utc', None)
        if utc is None:
            utc = self.__utc = self.__datetime.astimezone(timezones['utc'])
        kwargs = self.__extract_datetime_dict(utc)
        kwargs['timezone'] = 'utc'
        return self.__class__(**kwargs)
    
    @classmethod
    def now(cls, timezone='utc'):
        naive = datetime.datetime.utcnow()
        now = cls.from_datetime(naive, 'utc')
        now.timezone = timezone
        return now
    
    @property
    def datetime(self):
        return self.__datetime
    
    @property
    def timezone(self):
        return timezones[self.__timezone]
    
    @timezone.setter
    def timezone(self, timezone):
        self.__datetime = self.__datetime.astimezone(timezones[timezone])
        self.__timezone = timezone
        
    def __getattr__(self, attribute):
        # delegate to underlying datetime representation if it isn't defined
        try:
            value = self.__dict__[attribute]
        except:
            try:
                value = getattr(self.__datetime, attribute)
            except:
                message = '"{}" has no attribute "{}".'.format(self.__class__,
                                                               attribute)
                raise AttributeError(message)
        return value
        
    def __setattr__(self, attribute, value):
        if attribute in self.__immutables:
            raise AttributeError('Attribute "{}" is immutable.  Use the method '
                                 '```replace``` instead.'.format(attribute))
        else:
            super(When, self).__setattr__(attribute, value)
        
    @property
    def year(self):
        return self.__datetime.year
        
    @property
    def day(self):
        return self.__datetime.day
    
    @property
    def hour(self):
        return self.__datetime.hour
    
    @property
    def minute(self):
        return self.__datetime.minute
    
    @property
    def second(self):
        return self.__datetime.second
    
    @property
    def microsecond(self):
        return self.__datetime.microsecond
            
    def __dir__(self):
        pass
    
    def __str__(self):
        return str(self.__datetime)

    def __repr__(self):
        return repr(self.__datetime)
        
    def __sub__(self, other):
        pass
    
    def __add__(self, other):
        pass


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