# standard libraries
import datetime
import time
import warnings
import collections
# third party libraries
import pytz
# first party libraries
from . import (timezones, while_, substitutions)


While = while_.While


__all__ = ('When', 'now', 'parse', )


timezones = timezones.timezones


def _callable_attribute(value):
    """ A wrapper object that returns itself when called.
    
        This is useful for ensuring backwards compatibility with object methods
        that really ought to be properties.
        
        >>> class Test:
        ...     
        ...     @property
        ...     def property_and_method(self):
        ...         return _callable_attribute(1)
        ...
        >>> test = Test()
        >>> test.property_and_method
        1
        >>> test.property_and_method()
        1
        
    """
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
        are mutable and are treated as views on the underlying instant.
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
    def fromordinal(cls, ordinal, timezone='utc', dst=False):
        datetime = datetime.datetime.fromordinal(ordinal)
        return cls.from_datetime(datetime, timezone, dst)
    
    from_ordinal = fromordinal
        
    @classmethod
    def fromtimestamp(cls, timestamp, timezone='utc', dst=False):
        datetime = datetime.datetime.fromtimestamp(timestamp)
        return cls.from_datetime(datetime, timezone, dst)
    
    from_timestamp = fromtimestamp
    
    @classmethod
    def utcfromtimestamp(cls, timestamp):
        datetime = datetime.datetime.fromtimestamp(timestamp)
        return cls.from_datetime(datetime, timezone='utc')
        
    utc_from_timestamp = utcfromtimestamp
    
    @property
    def weekday(self):
        return _callable_attribute(self.__datetime.weekday())
        
    @property
    def tzinfo(self):
        return self.__datetime.tzinfo
        
    @property
    def utcoffset(self):
        return _callable_attribute(self.__datetime.utcoffset())
    
    utc_offset = utcoffset
    
    @property
    def dst(self):
        return _callable_attribute(self.__datetime.dst())
    
    @property
    def timestamp(self):
        return _callable_attribute(self.__datetime.timestamp())
        
    @property
    def toordinal(self):
        return _callable_attribute(self.__datetime.toordinal())
        
    ordinal = to_ordinal = toordinal
    
    @property
    def isoweekday(self):
        return _callable_attribute(self.__datetime.isoweekday())
        
    iso_weekday = isoweekday
        
    @property
    def isocalendar(self):
        return _callable_attribute(self.__datetime.isocalendar())
    
    iso_calendar = isocalendar
    
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
    def utcnow(cls):
        """ Construct a When at this very instant in the default UTC timezone.
            
        """
        return _callable_attribute(cls.now())
    
    utc_now = utcnow
    
    def timetuple(self):
        timetuple = self.__datetime.timetuple()
        return _callable_attribute(timetuple)
    
    time_tuple = timetuple
    
    def utctimetuple(self):
        timetuple = self.utc.__datetime.utctimetuple()
        return _callable_attribute(timetuple)
    
    utc_time_tuple = utctimetuple
    
    def ctime(self):
        ctime = self.__datetime.ctime()
        return _callable_attribute(ctime)
        
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
        """ Exposes the When instant in UTC as an attribute.
        
            This is cached upon first use given that it is invariant/immutable.
        
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
    
    def replace(self, **kwargs):
        datetime_dict = self.__extract_datetime_dict(self.__datetime)
        datetime_dict.update(kwargs)
        return self.__class__(**datetime_dict)
    
    @property
    def date(self):
        return _callable_attribute(self.__datetime.date())
    
    @property
    def today(self):
        return _callable_attribute(datetime.datetime.today())
        
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
        """ The minimum datetime instant that can be expressed on this platform.
            
            This is a simple proxy to the standard library datetime module.
            
        """
        return datetime.datetime.min
        
    @property
    def max(self):
        """ The maximum datetime instant that can be expressed on this platform.
        
            This is a simple proxy to the standard library datetime module.
            
        """
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
        timezone = timezones[self.__timezone]
        timezone.name = timezones[self.__timezone]
        return timezone
    
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
            '2015-04-22T00:00:00+00:00'
        
        """
        return _callable_attribute(self.__datetime.isoformat())
    
    iso_format = isoformat
    
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
    
    def strftime(self, specifier):
        return self.__datetime.strftime(specifier)
        
    @classmethod
    def strptime(cls, string, specifier, timezone='utc', dst=False):
        datetime = datetime.datetime.strptime(string, specifier)
        return cls.from_datetime(datetime, timezone, dst)
    
    @property
    def inflection(self):
        """ Return the inflected ordinal associated with the current date.
            
            >>> earth_day = When(year=2015, month=4, day=22, hour=5, 
            ...                  timezone='America/New_York')
            >>> '{}{} day of the month'.format(earth_day.day, 
            ...                                 earth_day.inflection)
            '22nd day of the month'
            
        """
        if self.day in set((1, 21, 31)):
            return 'st'
        if self.day in set((2, 22)):
            return 'nd'
        if self.day in set((3, 23)):
            return 'rd'
        return 'th'
    
    @property
    def day_of_year(self):
        """ The day of the year for this When instant.
            
            >>> earth_day = When(year=2015, month=4, day=22, hour=5, 
            ...                  timezone='America/New_York')

        """    
        #    >>> earth_day.day_of_year
        #    112
            
        
        return self.timetuple.tm_yday
    
    def __format__(self, specifier):
        """ Format a When instant as a string.
        
            Instead of having to refer back to a list of format directives
            like strftime, this implementation relies on a reference date.  The
            reference is the date of the American Declaration of Independence
            at 1:02:03.012345PM in Philadelphia.
            
            >>> reference = When(year=1776, month=7, day=4, hour=13, minute=2,
            ...                  second=3, microsecond=12345, 
            ...                  timezone='America/New_York')
            
            The following substitutions are made:
            
            * 1776:         four-digit year
            * 76:           two-digit year
            * July:         full month name
            * Jul:          abbreviated month name
            * 07:           zero-padded two-digit month
            * 7:            month
            * 04:           zero-padded two-digit day
            * 4:            day
            * th:           ordinal (ie, July 4__th__ or February 2__nd__)
            * Thu:          abbreviated weekday name
            * Thursday:     full weekday name
            * 01:           zero-padded two-digit hour (12-hour clock)
            * 1:            hour (12-hour clock)
            * 13:           zero-padded two-digit hour (24-hour clock)
            * p:            AM/PM formatted as a single lowercase character
            * PM:           AM/PM formatted as a two uppercase characters
            * 02:           zero-padded two-digit minute
            * 03:           zero-padded two-digit second
            * 012:          zero-padded three-digit millisecond
            * 12:           millisecond
            * 012345:       zero-padded six-digit microsecond
            * 12345:        microsecond
            * '-04:00':     utc offset
            * 'America/New_York': timezone name
            
            Here are some examples.
            
            >>> earth_day = When(year=2015, month=4, day=22, hour=5, minute=30,
            ...                  second=59, microsecond=23,
            ...                  timezone='America/Los_Angeles')
            >>> # iso8601 format
            >>> '{:1776-07-04T13:02:03.012345-04:00}'.format(earth_day)
            '2015-04-22T05:30:59.000023-07:00'
            >>> earth_day.iso_format()
            '2015-04-22T05:30:59.000023-07:00'
            
            
        """
        return substitutions.in_string(specifier, self._format_substitutions)
    
    @property
    def _format_substitutions(self):
        """ Dynamically compute a set of substitutions that transform the 
            reference date to the instant represented by this When.
        
            At some point, the substitution list and the regular expression 
            in __format__ should probably be cached for performance.
        
        """
        return collections.OrderedDict((
                            ('1776', self.strftime('%Y')),
                            ('76', self.strftime('%y')),
                            ('13', self.strftime('%H')),
                            ('012', self.strftime('%f')[:3]),
                            ('12', self.strftime('%f')[:3].lstrip()),
                            ('012345', self.strftime('%f')),
                            ('12345', self.strftime('%f').lstrip()),
                            ('-04:00', self.strftime('%z')),
                            ('July', self.strftime('%B')),
                            ('Jul', self.strftime('%b')),
                            ('07', self.strftime('%m')),
                            ('7', self.strftime('%m').lstrip()),
                            ('04', self.strftime('%d')),
                            ('4', self.strftime('%d').lstrip()),
                            ('th', self.inflection),
                            ('Thu', self.strftime('%a')),
                            ('Thursday', self.strftime('%A')),
                            ('01', self.strftime('%I')),
                            ('1', self.strftime('%I').lstrip()),
                            ('p', 'a' if self.hour < 12 else 'p'),
                            ('PM', 'AM' if self.hour < 12 else 'PM'),
                            ('P.M.', 'A.M.' if self.hour < 12 else 'P.M.'),
                            ('p.m.', 'a.m.' if self.hour < 12 else 'p.m.'),
                            ('02', self.strftime('%M')),
                            ('03', self.strftime('%S')),
                            ('America/New_York', self.timezone.name),
                    ))
    
    def __parse__(self, string, specifier):
        pass
    
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
        """ Support pickling.
        
            >>> # see __reduce__ for testing
        
        """
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
    """ Return a When object at this instant, with initial view set by 
        ```timezone```.
        
    """
    return When.now(timezone)


def parse(datetime, specifier='iso8601', timezone='utc'):
    if specifier == 'iso8601':
        return When.from_iso8601_string(datetime, timezone)
    else:
        return When.from_parsed_string(datetime, specifier, timezone)
