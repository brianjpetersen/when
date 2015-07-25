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
        
        While does not subclass ```datetime.timedelta```.  Instead, 
    """

    def __init__(self, years=0, months=0, days=0, hours=0, minutes=0, 
                 seconds=0, milliseconds=0, microseconds=0):
        pass

    @classmethod
    def from_timedelta(cls, timedelta):
        pass
    
    @property
    def timedelta(self):
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


def _callable_attribute(value):
    
    class Proxy(type(value)):
        
        def __new__(cls):
            return type(value).__new__(cls, value)
        
        def __call__(self):
            return value
            
    return Proxy()


class When(datetime.datetime):
    """ Python dates and times for humans.
    
        The API for the standard library datetime module is broken.  Datetimes 
        are timezone-naive by default.  Datetime objects are entirely immutable,
        including timezones, even though 5p in New York is the **same** instant
        as 2p in Los Angeles.  If my life depended on supplying a correct string 
        format specifier to strftime without consulting the documentation, 
        I'd start planning my funeral instead of even making an attempt.
        
        ```when.When``` addresses these issues, making dates and times more
        friendly and Pythonic.  Insomuch as possible, it maintains compatibility
        with the standard library datetime object (in both a duck-typing sense
        and an explicit ```isinstance```/```issubclass``` sense, although it is
        able to do a much better job at the latter due to the treatment of dst
        required for true timezone-awareness).
        
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
        
        ```when.When``` is a thin wrapper over a Python datetime object and
        Pytz.  It proxies most attribute access to an underlying timezone-aware 
        datetime object, and modifies constructors to handle timezone-awareness 
        by default.  It is immutable in the sense that attributes cannot be 
        modified that would change the unique instant the object represents
        (put more technically, the UTC datetime is invariant), but timezones
        are mutable and are treated as views.
    """
    
    __immutables = ('year', 'month', 'day', 'hour', 'minute', 'second', 
                    'microsecond')
                        
    def __new__(cls, *args, **kwargs):
        """ Construct a When instance.
        
            We need to subclass from datetime.datetime to allow the following 
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
        """ Initialize When instance.
        
        """
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
            When(2015, 1, 1, 0, 0, 0, 0, 'UTC')
            >>> d = datetime.datetime(2015, 1, 1, tzinfo=timezones['America/New_York'])
            >>> warnings.filterwarnings('error')
            >>> When.from_datetime(d, 'utc')
            Traceback (most recent call last):
              File "/usr/lib/python3.4/doctest.py", line 1324, in __run
                compileflags, 1), test.globs)
              File "<doctest when.when.When.from_datetime[4]>", line 1, in <module>
                When.from_datetime(d, 'utc')
              File "/home/ubuntu/workspace/when/when/when.py", line 0, in from_datetime
                warnings.warn(warning)
            UserWarning: Note, this datetime is not naive, and the tzinfo America/New_York associated with it is being ignored in favor of the supplied timezone utc.
            >>> warnings.filterwarnings('ignore')
            >>> When.from_datetime(d, 'utc')
            When(2015, 1, 1, 0, 0, 0, 0, 'UTC')
            
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
        
    def __iter__(self):
        utc = self.utc
        for attribute in self.__immutables:
            yield getattr(utc, attribute)
    
    @classmethod
    def now(cls, timezone='utc'):
        """ Construct a When at this very instant.
        
            The optarg ```timezone``` can be used to set the initial timezone
            view.  Because ```now``` is computed in UTC, there are no daylight
            saving time transitions to be worried about, and we don't need to 
            supply kwarg ```dst```.
            
            >>> d = datetime.datetime.utcnow()
            >>> w = When.now()
            >>> (d.year, d.month, d.day, d.hour, d.minute, d.second) == \
                (w.year, w.month, w.day, w.hour, w.minute, w.second)
            True
            
        """
        naive = datetime.datetime.utcnow()
        now = cls.from_datetime(naive, 'utc')
        now.timezone = timezone
        return now
        
    @classmethod
    def __extract_datetime_dict(cls, datetime):
        """ Convenience method that returns immutable When attributes as dict.
        
        """
        datetime_dict = {}
        for attribute in cls.__immutables:
            try:
                datetime_dict[attribute] = getattr(datetime, attribute)
            except:
                continue
        return datetime_dict
    
    @property
    def utc(self):
        """ A convenience attribute to expose the When instant in UTC.
        
            This is cached upon first use.
        
            >>> earth_day = When(year=2015, month=4, day=22, hour=5, 
            ...                  timezone='America/New_York')
            >>> print(earth_day.utc)
            2015-04-22 09:00:00+00:00
            >>> earth_day.timezone = 'utc'
            >>> print(earth_day.utc)
            2015-04-22 09:00:00+00:00
        
        """
        utc = getattr(self, '__utc', None)
        if utc is None:
            utc = self.__utc = self.__datetime.astimezone(timezones['utc'])
        kwargs = self.__extract_datetime_dict(utc)
        kwargs['timezone'] = 'utc'
        return self.__class__(**kwargs)
        
    @classmethod
    def replace(cls, *kwargs):
        raise NotImplemented
    
    @property
    def date(self):
        raise NotImplemented
    
    @property
    def today(self):
        raise NotImplemented
        
    def __setattr__(self, attribute, value):
        """ Handle attribute assignment.
        
            This is necessary to enforce immutability.
        
        """
        if attribute in self.__immutables:
            raise AttributeError('Attribute "{}" is immutable.  Use the method '
                                 '```replace``` instead.'.format(attribute))
        else:
            super(When, self).__setattr__(attribute, value)
    
    @property
    def min(self):
        return datetime.datetime.min
        
    @property
    def max(self):
        return datetime.datetime.max

    @property
    def datetime(self):
        """ Retrieve the instant represented as a standard library datetime.
        
            Note, because datetime considers instants different depending 
            on the timezone, the value returned here is dependent on the current
            timezone view.
            
        """
        return self.__datetime
    
    @property
    def timezone(self):
        """ Retrieve the mutable timezone.
        
        """
        return timezones[self.__timezone]
    
    @timezone.setter
    def timezone(self, timezone):
        """ Set the mutable timezone, which changes the *view* on the instant.
        
            >>> earth_day = When(year=2015, month=4, day=22, hour=5, 
            ...                  timezone='America/New_York')
            >>> print(earth_day)
            2015-04-22 05:00:00-04:00
            >>> earth_day.timezone = 'America/Los_Angeles'
            >>> print(earth_day)
            2015-04-22 02:00:00-07:00
            >>> earth_day.timezone
            <DstTzInfo 'America/Los_Angeles' LMT-1 day, 16:07:00 STD>
        
        """
        self.__datetime = self.__datetime.astimezone(timezones[timezone])
        self.__timezone = timezone
    
    @property
    def isoformat(self):
        """ Return the instant in the timezone view in ISO-8601 format.
        
            Note, this is implemented as both a method-like callable for 
            compatibility with the ```datetime``` object and as a property
            for convenience
            
            >>> earth_day = When(2015, 4, 22, timezone='utc')
            >>> earth_day.isoformat
            '2015-04-22T00:00:00+00:00'
            >>> earth_day.isoformat()
            
        
        """
        return _callable_attribute(self.__datetime.isoformat())
    
    @property
    def year(self):
        """ Immutable year attribute.
        
            >>> sometime = When(9999, 8, 7, 6, 5, 4, 333333)
            >>> sometime.year
            9999
        
        """
        return self.__datetime.year
        
    @property
    def month(self):
        """ Immutable month attribute.
        
            >>> sometime = When(9999, 8, 7, 6, 5, 4, 333333)
            >>> sometime.month
            8
        
        """
        return self.__datetime.month
        
    @property
    def day(self):
        """ Immutable day attribute.
        
            >>> sometime = When(9999, 8, 7, 6, 5, 4, 333333)
            >>> sometime.day
            7
        
        """
        return self.__datetime.day
    
    @property
    def hour(self):
        """ Immutable hour attribute.
        
            >>> sometime = When(9999, 8, 7, 6, 5, 4, 333333)
            >>> sometime.hour
            6
        
        """
        return self.__datetime.hour
    
    @property
    def minute(self):
        """ Immutable minute attribute.
        
            >>> sometime = When(9999, 8, 7, 6, 5, 4, 333333)
            >>> sometime.minute
            5
        
        """
        return self.__datetime.minute
    
    @property
    def second(self):
        """ Immutable second attribute.
        
            >>> sometime = When(9999, 8, 7, 6, 5, 4, 333333)
            >>> sometime.second
            4
        
        """
        return self.__datetime.second
    
    @property
    def microsecond(self):
        """ Immutable microsecond attribute.
        
            >>> sometime = When(9999, 8, 7, 6, 5, 4, 333333)
            >>> sometime.microsecond
            333333
        
        """
        return self.__datetime.microsecond
    
    def __str__(self):
        """ Return a string representation of the When instance.
            
            >>> str(When(2015, 1, 2, 3, 4, 5))
            '2015-01-02 03:04:05+00:00'
            
        """
        return str(self.__datetime)

    def __repr__(self):
        """ Return a string that can be used to reproduce this When instance.
            
            >>> repr(When(2015, 1, 2, 3, 4, 5, 666666))
            "When(2015, 1, 2, 3, 4, 5, 666666, 'UTC')"
            
        """
        return '{}{}'.format(self.__class__.__name__, 
                             tuple(self) + (self.__timezone.upper(), ))
        
    def __sub__(self, other):
        # other most be When => returns While
        # other must be While => returns When
        pass
    
    def __rsub__(self, other):
        pass
    
    def __add__(self, other):
        # other must be timedelta or While
        # returns When
        pass
    
    def __radd__(self, other):
        pass
    
    def __getnewargs__(self):
        """ Support efficient pickling by minimal attribute persistence.
        
            >>> import pickle
            >>> now = When.now()
            >>> now == pickle.loads(pickle.dumps(now))
            True
        
        """
        utc = self.utc
        return tuple(utc) + ('utc', )
    
    def __getstate__(self):
        """ Support efficient pickling by minimal attribute persistence.
        
            >>> # see __getstate__ for testing
        
        """
        return {'timezone': self.__timezone}
        
    def __setstate__(self, state):
        """ Support efficient pickling by minimal attribute persistence.
        
            >>> # see __getstate__ for testing
        
        """
        utc = state['utc']
        self.timezone = timezone
    
    def __eq__(self, other):
        """ Returns equivalence against other When-like objects.
        
            >>> When(2015, 1, 1) == When(2015, 1, 1)
            True
            >>> new_york = When(2015, 1, 1, 12, timezone='America/New_York')
            >>> los_angeles = When(2015, 1, 1, 9, timezone='America/Los_Angeles')
            >>> new_york == los_angeles
            True
        
        """
        return tuple(self) == tuple(other)
        
    def __ne__(self, other):
        """ Returns non-equivalence against other When-like objects.
        
            >>> When(2015, 1, 1) != When(2015, 12, 31)
            True
            
        """
        return tuple(self) != tuple(other)
        
    def __gt__(self, other):
        """ Returns greater than operator against other When-like objects.
        
            >>> When(2015, 1, 1) > When(2015, 12, 31)
            False
            
        """
        return tuple(self) > tuple(other)
        
    def __ge__(self, other):
        """ Returns greater than or equal operator against When-like objects.
        
            >>> When(2015, 1, 1) >= When(2015, 1, 1)
            True
            
        """
        return tuple(self) >= tuple(other)
    
    def __lt__(self, other):
        """ Returns less than operator against other When-like objects.
        
            >>> When(2015, 1, 1) < When(2015, 1, 1)
            False
            
        """
        return tuple(self) < tuple(other)
        
    def __le__(self, other):
        """ Returns less than or equal operator against When-like objects.
        
            >>> When(2015, 1, 1) <= When(2015, 1, 1)
            True
            
        """
        return tuple(self) <= tuple(other)
    
    def __hash__(self):
        """ Return the hash of a When instance.
        
            The unique instant represented by a When is defined unambiguously
            by a hash of the utc immutable attributes (returned by __iter__).
        
        """
        return hash(tuple(self))
    
    @property
    def resolution(self):
        """ The resolution of When (and datetime) objects on this platform.
        
            TODO: this should really return a While instead of a timedelta.
        
        """
        return datetime.datetime.resolution
    
    # pickle-related
    
    def __getstate__(self):
        return {'timezone': self.__timezone}
        
    def __setstate__(self, state):
        """ Support pickling.
        
            >>> # see __reduce__ for testing
        
        """
        self.timezone = state['timezone']
    
    def __reduce__(self):
        """ Support pickling.
        
            >>> import pickle
            >>> now = When.now()
            >>> now == pickle.loads(pickle.dumps(now))
            True
            >>> earth_day = When(2015, 4, 22, timezone='America/New_York')
            >>> earth_day == pickle.loads(pickle.dumps(earth_day))
            True
            >>> earth_day = pickle.loads(pickle.dumps(earth_day))
            >>> print(earth_day, earth_day.timezone)
            2015-04-22 00:00:00-04:00 America/New_York
            
        """
        return (self.__class__, tuple(self.utc) + ('utc', ), 
                self.__getstate__())


def now(timezone='utc'):
    """ Return a When object at this instant, with initial view set by ```timezone```.
        
    """
    return When.now(timezone)


def parse(datetime, specifier='iso8601', timezone='utc'):
    if specifier == 'iso8601':
        return When.from_iso8601_string(datetime, timezone)
    else:
        return When.from_parsed_string(datetime, specifier, timezone)


def sleep(seconds):
    time.sleep(seconds)