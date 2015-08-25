# standard libraries
import datetime
import calendar
import pickle
import collections
import re
# third party libraries
import pytz
# first party libraries
from . import (timezones, while_, substitutions, )


__all__ = ('When', 'now', 'parse', )


While = while_.While
timezones = timezones.timezones


def _scrub_potentials(*potentials):
    potentials = [potential for potential in potentials if potential is not None]
    if len(potentials) == 0:
        return None
    first = potentials[0]
    if not all(first == potential for potential in potentials):
        raise pytz.AmbiguousTimeError()
    return first


class ParsingError(ValueError):

    pass


class NotNoneDict(collections.MutableMapping):

    def __init__(self, defaults):
        self._mapping = {}
        self._mapping.update(defaults)

    def __getitem__(self, item):
        return self._mapping[item]

    def __setitem__(self, item, value):
        if item in self._mapping:
            if value is not None:
                self._mapping[item] = value
            else:
                pass
        else:
            self._mapping[item] = value

    def __delitem__(self, item):
        del self._mapping[item]

    def __iter__(self):
        return iter(self._mapping)

    def __len__(self):
        return len(self._mapping)

    def __str__(self):
        return str(self._mapping)

    def __repr__(self):
        return repr(self._mapping)


class When(object):
    """ Python dates and times for humans.
    
        The API for the standard library datetime module is broken.  Datetimes 
        are timezone-naive by default.  Datetime objects are entirely immutable,
        including timezones, even though 5p in New York is the **same** instant
        as 2p in Los Angeles.  If my life depended on supplying a correct string 
        format specifier to strftime without consulting the documentation, 
        I'd start planning my funeral.
        
        when.When addresses these issues, making dates and times more
        friendly and Pythonic.
        
        >>> earth_day = When(year=2015, month=4, day=22, hour=5, 
        ...                  timezone='America/New_York')
        >>> print(earth_day)
        2015-04-22 05:00:00-04:00
        >>> earth_day.timezone = 'America/Los_Angeles'
        >>> print(earth_day)
        2015-04-22 02:00:00-07:00
        >>> earth_day.timezone
        <DstTzInfo 'America/Los_Angeles' LMT-1 day, 16:07:00 STD>
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
    def __init__(self, year, month, day, hour=0, minute=0, second=0, 
                 microsecond=0, timezone=None, dst_if_ambiguous=None):
        if timezone is None or timezone not in timezones:
            raise ValueError('You must supply a valid timezone.')
        naive = datetime.datetime(year, month, day, hour, minute, 
                                  second, microsecond)
        self._datetime = timezones[timezone].localize(naive, dst_if_ambiguous)
        self._utc = self._datetime.astimezone(timezones['utc'])
        self._timezone = timezone
        self._format_substitutor = None
        
    # class constructors

    @classmethod
    def now(cls, timezone='utc'):
        """ Construct a When at this very instant.
        
            The optarg ```timezone``` can be used to set the initial timezone
            view.  Because ```now``` is computed in UTC, there are no daylight
            saving time transitions to be worried about, and we don't need to 
            supply kwarg ```dst_if_ambiguous```.
            
            >>> d = datetime.datetime.utcnow()
            >>> w = When.now()
            >>> (d.year, d.month, d.day, d.hour, d.minute, d.second) == \
                (w.year, w.month, w.day, w.hour, w.minute, w.second)
            True
            
        """
        utc = datetime.datetime.utcnow()
        when = cls.from_datetime(utc, 'utc')
        if timezones[timezone] != timezones['utc']:
            when.timezone = timezone
        return when

    @classmethod
    def from_datetime(cls, datetime, timezone, dst_if_ambiguous=None):
        """ Construct a When from a standard-library datetime and a timezone.
        
            Note, any naive tzinfo supplied as part of the datetime will result 
            in an Exception being issued.
            
            >>> d = datetime.datetime(2015, 1, 1)
            >>> When.from_datetime(d, 'utc')
            When(2015, 1, 1, 0, 0, 0, 0, 'utc', False)
            >>> d = datetime.datetime(2015, 1, 1, tzinfo=timezones['America/New_York'])
            >>> When.from_datetime(d, 'utc')
            Traceback (most recent call last):
            ...
            AmbiguousTimeError: Cowardly refusing to ignore the supplied datetime's tzinfo in favor of the supplied timezone.
            >>> d = d.replace(tzinfo=None)
            >>> When.from_datetime(d, 'utc')
            When(2015, 1, 1, 0, 0, 0, 0, 'utc', False)
            
        """
        if datetime.tzinfo is not None:
            warning = ('Cowardly refusing to ignore the supplied datetime\'s '
                       'tzinfo in favor of the supplied timezone.')
            raise pytz.AmbiguousTimeError(warning)
        kwargs = cls._dict_from_datetime(datetime)
        kwargs['timezone'] = timezone
        kwargs['dst_if_ambiguous'] = dst_if_ambiguous
        return cls(**kwargs)
    
    @classmethod
    def from_string(cls, string, specifier, century=None, year=None, month=None, 
                    day=None, hour=0, minute=0, second=0, millisecond=0, 
                    microsecond=0, meridian=None, timezone=None, 
                    dst_if_ambiguous=None):
        """ Construct a When from a string and a specifier.
            
            >>> When.from_string('2015-03-03 02:58:59', 
            ...                  '1776-07-04 01:02:03', timezone='utc')
            When(2015, 3, 3, 2, 58, 59, 0, 'utc', False)
            >>> When.from_string('2015-03-03 2:00:59.222222z a.m.', 
            ...                  '1776-07-04 1:02:03.012345America/New_York p.m.')
            When(2015, 3, 3, 2, 0, 59, 222222, 'utc', False)
            
        """
        # pre-processing
        if millisecond is not None and microsecond is None:
            microsecond = 1000*millisecond
        elif millisecond is not None and microsecond is not None:
            if 1000*millisecond != microsecond:
                raise pytz.AmbiguousTimeError()
        # first pass of substitutions on specifier to prepare regex
        substitutions_for_regex = {
            '1776': r'(?P<_1776>\d?\d?\d?\d)',
            '76': r'(?P<_76>\d\d)',
            'July': r'(?P<_July>January|February|March|April|May|June|July|August|September|October|November|December)',
            'Jul': r'(?P<_Jul>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',
            'America/New_York': r'(?P<timezone>Z|z|[a-zA-Z_/]+)',
            '012345': r'(?P<_012345>\d\d\d\d\d\d)',
            '12345': r'(?P<_12345>\d?\d?\d?\d?\d?\d)',
            '012': r'(?P<_012>\d\d\d)',
            '12': r'(?P<_12>\d?\d?\d)',
            '13': r'(?P<_13>\d\d)',
            '07': r'(?P<_07>\d\d)',
            '04': r'(?P<_04>\d\d)',
            '03': r'(?P<_03>\d\d)',
            '02': r'(?P<_02>\d\d)',
            '01': r'(?P<_01>\d\d)',
            '7': r'(?P<_7>\d?\d)',
            '4': r'(?P<_4>\d?\d)',
            '3': r'(?P<_3>\d?\d)',
            '2': r'(?P<_2>\d?\d)',
            '1': r'(?P<_1>\d?\d)',
            'pm': r'(?P<_pm>am|pm)',
            'p.m.': r'(?P<_p_m_>a\.m\.|p\.m\.)',
            'PM': r'(?P<_PM>AM|PM)',
            'P.M.': r'(?P<_P_M_>A\.M\.|P\.M\.)',
        }
        # iterate over specifiers and return first match
        required_matches = ('year', 'month', 'day', 'timezone')
        matched = NotNoneDict({
            'year': year,
            'month': month,
            'day': day,
            'hour': hour,
            'minute': minute,
            'second': second,
            'microsecond': microsecond,
            'timezone': timezone,
            'dst_if_ambiguous': dst_if_ambiguous,
        })  
        regex = substitutions.in_string(specifier, substitutions_for_regex)
        match = re.match(regex, string)
        if match is None:
            raise ParsingError()
        unprocessed_matches = match.groupdict()
        # process year
        year_from_1776 = unprocessed_matches.get('_1776', None)
        decade_from_76 = unprocessed_matches.get('_76', None)
        _year_tuple = cls._process_year(year_from_1776, decade_from_76, century)
        matched['year'] = _scrub_potentials(*_year_tuple)
        # process month
        month_from_July = unprocessed_matches.get('_July', None)
        month_from_Jul = unprocessed_matches.get('_Jul', None)
        month_from_07 = unprocessed_matches.get('_07', None)
        month_from_7 = unprocessed_matches.get('_7', None)
        _month_tuple = cls._process_month(month_from_July, month_from_Jul, month_from_07, 
                                          month_from_7)
        matched['month'] = _scrub_potentials(*_month_tuple)
        # day
        day_from_04 = unprocessed_matches.get('_04', None)
        day_from_4 = unprocessed_matches.get('_4', None)
        _day_tuple = cls._process_day(day_from_04, day_from_4)
        matched['day'] = _scrub_potentials(*_day_tuple)
        # hour
        hour_from_13 = unprocessed_matches.get('_13', None)
        hour_from_01 = unprocessed_matches.get('_01', None)
        hour_from_1 = unprocessed_matches.get('_1', None)
        meridian_from_pm = unprocessed_matches.get('_pm', None)
        meridian_from_p_m_ = unprocessed_matches.get('_p_m_', None)
        meridian_from_PM = unprocessed_matches.get('_PM', None)
        meridian_from_P_M_ = unprocessed_matches.get('_P_M_', None)
        _hour_tuple = cls._process_hour(hour_from_13, hour_from_01, hour_from_1, 
                                        meridian_from_pm, meridian_from_p_m_, 
                                        meridian_from_PM, meridian_from_P_M_)
        matched['hour'] = _scrub_potentials(*_hour_tuple)
        # minute
        minute_from_02 = unprocessed_matches.get('_02', None)
        minute_from_2 = unprocessed_matches.get('_2', None)
        _minute_tuple = cls._process_minute(minute_from_02, minute_from_2)
        matched['minute'] = _scrub_potentials(*_minute_tuple)
        # second
        second_from_03 = unprocessed_matches.get('_03', None)
        second_from_3 = unprocessed_matches.get('_3', None)
        _second_tuple = cls._process_second(second_from_03, second_from_3)
        matched['second'] = _scrub_potentials(*_second_tuple)
        # millisecond and microsecond
        millisecond_from_012 = unprocessed_matches.get('_012', None)
        millisecond_from_12 = unprocessed_matches.get('_12', None)
        microsecond_from_12345 = unprocessed_matches.get('_12345', None)
        microsecond_from_012345 = unprocessed_matches.get('_012345', None)
        _microsecond_tuple = cls._process_fractional_sections(millisecond_from_012, 
                                                              millisecond_from_12, 
                                                              microsecond_from_12345, 
                                                              microsecond_from_012345)
        matched['microsecond'] = _scrub_potentials(*_microsecond_tuple)
        # timezone
        timezone_from_America_New_York = unprocessed_matches.get('timezone', None)
        matched['timezone'] = cls._process_timezone(timezone_from_America_New_York)
        # 
        return cls(**matched)

    @classmethod
    def from_iso_format(cls, string, timezone=None, dst_if_ambiguous=None):
        """ Construct a When from the 
            
            >>> When.from_iso_format('2015-03-03T02:00:59', timezone='utc')
            When(2015, 3, 3, 2, 0, 59, 0, 'utc', False)
            >>> When.from_iso_format('2015-03-03T02:00:59.123422Z', timezone='utc')
            When(2015, 3, 3, 2, 0, 59, 123422, 'utc', False)
                        
        """
        specifiers = (
                          '1776[-]?07[-]?04[T ]?13[:]?02[:]?03.012345America/New_York',
                          '1776[-]?07[-]?04[T ]?13[:]?02[:]?03.0123America/New_York',
                          '1776[-]?07[-]?04[T ]?13[:]?02[:]?03America/New_York',
                          '1776[-]?07[-]?04America/New_York',
                          '1776[-]?07[-]?04[T ]?13[:]?02[:]?03.012345',
                          '1776[-]?07[-]?04[T ]?13[:]?02[:]?03.0123',
                          '1776[-]?07[-]?04[T ]?13[:]?02[:]?03',
                          '1776[-]?07[-]?04',
                      )
        for specifier in specifiers:
            try:
                return cls.from_string(string, specifier, timezone=timezone, 
                                       dst_if_ambiguous=dst_if_ambiguous)
            except:
                continue
        raise ParsingError()

    # process support
    
    @staticmethod
    def _process_year(year_from_1776, decade_from_76, century):
        # pre-process
        if decade_from_76 is not None:
            if century is None:
                raise pytz.ValueError()
            year_from_76 = century + int(decade_from_76)
        else:
            year_from_76 = None
        if year_from_1776 is not None:
            year_from_1776 = int(year_from_1776)
            if century is not None:
                if abs(year_from_1776 - century) > 100:
                    raise pytz.AmbiguousTimeError()
        # return year, catching any ambiguities
        return (year_from_1776, year_from_76)
    
    @staticmethod
    def _process_month(month_from_July, month_from_Jul, month_from_07, month_from_7):
        month_to_int = {
            'January': 1,
            'Jan': 1,
            'February': 2,
            'Feb': 2,
            'March': 3,
            'Mar': 3,
            'April': 4,
            'Apr': 4,
            'May': 5,
            'June': 6,
            'Jun': 6,
            'July': 7,
            'Jul': 7,
            'August': 8,
            'Aug': 8,
            'September': 9,
            'Sep': 9,
            'October': 10,
            'Oct': 10,
            'November': 11,
            'Nov': 11,
            'December': 12,
            'Dec': 12,
            None: None
        }
        month_from_July = month_to_int[month_from_July]
        month_from_Jul = month_to_int[month_from_Jul]
        if month_from_07 is not None:
            month_from_07 = int(month_from_07)
        if month_from_7 is not None:
            month_from_7 = int(month_from_7)
        # return month, catching any ambiguities
        return (month_from_July, month_from_Jul, month_from_07, month_from_7)
    
    @staticmethod
    def _process_day(day_from_04, day_from_4):
        # pre-process
        if day_from_04 is not None:
            day_from_04 = int(day_from_04)
        if day_from_4 is not None:
            day_from_4 = int(day_from_4)
        # return day, catching any ambiguities
        return (day_from_04, day_from_4)
    
    @staticmethod
    def _process_hour(hour_from_13, hour_from_01, hour_from_1, meridian_from_pm,
                      meridian_from_p_m_, meridian_from_PM, meridian_from_P_M_):
        # pre-process
        if meridian_from_pm is not None:
            if meridian_from_pm == 'pm':
                meridian_from_pm = 12
            else: # am
                meridian_from_pm = 0
        if meridian_from_p_m_ is not None:
            if meridian_from_p_m_ == 'p.m.':
                meridian_from_p_m_ = 12
            else: # a.m.
                meridian_from_p_m_ = 0
        if meridian_from_PM is not None:
            if meridian_from_PM == 'PM':
                meridian_from_PM = 12
            else: # AM
                meridian_from_PM = 0
        if meridian_from_P_M_ is not None:
            if meridian_from_P_M_ == 'P.M.':
                meridian_from_P_M_ = 12
            else: # AM
                meridian_from_P_M_ = 0
        meridian_offset = _scrub_potentials(meridian_from_pm, meridian_from_p_m_, 
                                            meridian_from_PM, meridian_from_P_M_)
        if meridian_offset is None:
            meridian_offset = 0
        if hour_from_13 is not None:
            hour_from_13 = int(hour_from_13)
        if hour_from_01 is not None:
            hour_from_01 = meridian_offset + int(hour_from_01)
        if hour_from_1 is not None:
            hour_from_1 = meridian_offset + int(hour_from_1)
        # return hour, catching any ambiguities
        return (hour_from_13, hour_from_01, hour_from_1)
    
    @staticmethod
    def _process_minute(minute_from_02, minute_from_2):
        # pre-process
        if minute_from_02 is not None:
            minute_from_02 = int(minute_from_02)
        if minute_from_2 is not None:
            minute_from_2 = int(minute_from_2)
        # return minute, catching any ambiguities
        return (minute_from_02, minute_from_2)
    
    @staticmethod
    def _process_second(second_from_03, second_from_3):
        # pre-process
        if second_from_03 is not None:
            second_from_03 = int(second_from_03)
        if second_from_3 is not None:
            second_from_3 = int(second_from_3)
        # return second, catching any ambiguities
        return (second_from_03, second_from_3)
    
    @staticmethod
    def _process_fractional_sections(millisecond_from_012, millisecond_from_12, microsecond_from_12345,
                                     microsecond_from_012345):
        # pre-process
        if millisecond_from_012 is not None:
            millisecond_from_012 = 1000*int(millisecond_from_012)
        if millisecond_from_12 is not None:
            millisecond_from_12 = 1000*int(millisecond_from_12)
        if microsecond_from_12345 is not None:
            microsecond_from_12345 = int(microsecond_from_12345)
        if microsecond_from_012345 is not None:
            microsecond_from_012345 = int(microsecond_from_012345)
        # return second, catching any ambiguities
        return (millisecond_from_012, millisecond_from_12, microsecond_from_12345,
                microsecond_from_012345)
    
    @staticmethod
    def _process_timezone(timezone_from_America_New_York):
        if timezone_from_America_New_York in ('z', 'Z'):
            return 'utc'
        else:
            return timezone_from_America_New_York

    # timezone-related

    @property
    def timezone(self):
        """ Retrieve the mutable timezone.
        
        """
        timezone = timezones[self._timezone]
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
        _tz = timezones[timezone]
        self._datetime = _tz.normalize(self._utc.astimezone(_tz))
        self._timezone = timezone
        self._format_substitor = None

    @property
    def dst(self):
        dst_integer = self.datetime.timetuple().tm_isdst
        if dst_integer == 1:
            return True
        elif dst_integer == 0:
            return False
        else:
            raise ValueError()

    # intrinsic properties

    @property
    def resolution(self):
        """ The resolution of When (and datetime) objects on this platform.
        
        """
        raise NotImplementedError() # this should really return a While instead of a timedelta
        return datetime.datetime.resolution

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

    # formatting

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
            * th:           ordinal (ie, July 4*th* or February 2*nd*)
            * Thu:          abbreviated weekday name
            * Thursday:     full weekday name
            * 01:           zero-padded two-digit hour (12-hour clock)
            * 1:            hour (12-hour clock)
            * 13:           zero-padded two-digit hour (24-hour clock)
            * PM:           AM/PM formatted as a two uppercase characters
            * 02:           zero-padded two-digit minute
            * 03:           zero-padded two-digit second
            * 012:          zero-padded three-digit millisecond
            * 12:           millisecond
            * 012345:       zero-padded six-digit microsecond
            * 12345:        microsecond
            * '-04:00':     utc offset
            * '-04':        utc offset
            * '-0400':      utc offset
            * 'America/New_York': timezone name
            
            Here are some examples.
            
            >>> earth_day = When(year=2015, month=4, day=22, hour=5, minute=30,
            ...                  second=59, microsecond=23,
            ...                  timezone='America/Los_Angeles')
            >>> '{:1776-07-04T13:02:03.012345-04:00}'.format(earth_day)
            '2015-04-22T05:30:59.000023-07:00'
            >>> earth_day.format_as_iso(precision='microseconds')
            '2015-04-22T05:30:59.000023-07:00'
            >>> '{:76/07/04}'.format(earth_day)
            '15/04/22'
            >>> 'Late {:July} back in `{:76}, what a very special time for me.'.format(earth_day, earth_day)
            'Late April back in `15, what a very special time for me.'
            >>> '{:2 minutes} past {:1pm}'.format(earth_day, earth_day)
            '30 minutes past 5am'

        """
        return self.format_substitutor(specifier)
    
    def _update_format_substitutor(self):
        format_substitutions = {
            '1776': self.datetime.strftime('%Y'),
            '012345': self.datetime.strftime('%f'),
            '12345': self.datetime.strftime('%f').lstrip('0'),
            '012': self.datetime.strftime('%f')[:3],
            '76': self.datetime.strftime('%y'),
            '13': self.datetime.strftime('%H'),
            '12': self.datetime.strftime('%f')[:3].lstrip('0'),
            '-04:00': '{}:{}'.format(self.datetime.strftime('%z')[:-2], self.datetime.strftime('%z')[-2:]),
            '-0400': self.datetime.strftime('%z'),
            'July': self.datetime.strftime('%B'),
            'Jul': self.datetime.strftime('%b'),
            '01': self.datetime.strftime('%I'),
            '02': self.datetime.strftime('%M'),
            '03': self.datetime.strftime('%S'),
            '04': self.datetime.strftime('%d'),
            '07': self.datetime.strftime('%m'),
            '1': self.datetime.strftime('%I').lstrip('0'),
            '2': self.datetime.strftime('%M').lstrip('0'),
            '3': self.datetime.strftime('%S').lstrip('0'),
            '4': self.datetime.strftime('%d').lstrip('0'),
            '7': self.datetime.strftime('%m').lstrip('0'),
            'America/New_York': self._timezone,
            'Thursday': self.datetime.strftime('%A'),
            'Thu': self.datetime.strftime('%a'),
            'th': self.inflection,
            'PM': 'AM' if self.hour < 12 else 'PM',
            'P.M.': 'A.M.' if self.hour < 12 else 'P.M.',
            'pm': 'am' if self.hour < 12 else 'pm',
            'p.m.': 'a.m.' if self.hour < 12 else 'p.m.',
        }
        self._format_substitutor = substitutions.Substitutor(format_substitutions)

    @property
    def format_substitutor(self):
        """ Dynamically compute a set of substitutions that transform the 
            reference date to the instant represented by this When.
        
        """
        if self._format_substitutor is None:
            self._update_format_substitutor()
        return self._format_substitutor

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
            inflection = 'st'
        elif self.day in set((2, 22)):
            inflection = 'nd'
        elif self.day in set((3, 23)):
            inflection = 'rd'
        else:
            inflection = 'th'
        return inflection

    # fundamental attributes

    @property
    def datetime(self):
        """ Retrieve the instant represented as a standard library datetime.
        
            Note, because datetime considers instants different depending 
            on the timezone, the value returned here is dependent on the current
            timezone view.
            
        """
        return self._datetime

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
        try:
            utc = self._when_utc
        except AttributeError:
            cls = self.__class__
            utc = cls.from_datetime(self._utc.replace(tzinfo=None), 'utc')
            self._when_utc = utc
        return self._when_utc

    @property
    def year(self):
        """ Immutable year attribute.
        
            >>> sometime = When(9999, 8, 7, 6, 5, 4, 333333, timezone='utc')
            >>> sometime.year
            9999
        
        """
        return self.datetime.year

    @year.setter
    def year(self, year):
        cls = self.__class__
        raise NotImplementedError() # return calendar math (similar to replace)

    @property
    def month(self):
        """ Immutable month attribute.
        
            >>> sometime = When(9999, 8, 7, 6, 5, 4, 333333, timezone='utc')
            >>> sometime.month
            8
        
        """
        return self.datetime.month

    @month.setter
    def month(self, month):
        cls = self.__class__
        raise NotImplementedError() # for ones like this, should you be able to do d.month += 13?

    @property
    def day(self):
        """ Immutable day attribute.
        
            >>> sometime = When(9999, 8, 7, 6, 5, 4, 333333, timezone='utc')
            >>> sometime.day
            7
        
        """
        return self.datetime.day

    @day.setter
    def day(self, day):
        cls = self.__class__
        raise NotImplementedError() # ditto

    @property
    def hour(self):
        """ Immutable hour attribute.
        
            >>> sometime = When(9999, 8, 7, 6, 5, 4, 333333, timezone='utc')
            >>> sometime.hour
            6
        
        """
        return self.datetime.hour

    @hour.setter
    def hour(self, hour):
        cls = self.__class__
        raise NotImplementedError()

    @property
    def minute(self):
        """ Immutable minute attribute.
        
            >>> sometime = When(9999, 8, 7, 6, 5, 4, 333333, timezone='utc')
            >>> sometime.minute
            5
        
        """
        return self.datetime.minute

    @minute.setter
    def minute(self, minute):
        cls = self.__class__
        raise NotImplementedError()

    @property
    def second(self):
        """ Immutable second attribute.
        
            >>> sometime = When(9999, 8, 7, 6, 5, 4, 333333, timezone='utc')
            >>> sometime.second
            4
        
        """
        return self.datetime.second

    @second.setter
    def second(self, second):
        cls = self.__class__
        raise NotImplementedError()

    @property
    def millisecond(self):
        """ Immutable millisecond attribute.
        
            >>> sometime = When(9999, 8, 7, 6, 5, 4, 333333, timezone='utc')
            >>> sometime.millisecond
            333.333
        
        """
        return self.datetime.microsecond/1000.0

    @millisecond.setter
    def millisecond(self, millisecond):
        cls = self.__class__
        raise NotImplementedError()

    @property
    def microsecond(self):
        """ Immutable microsecond attribute.
        
            >>> sometime = When(9999, 8, 7, 6, 5, 4, 333333, timezone='utc')
            >>> sometime.microsecond
            333333
        
        """
        return self.datetime.microsecond

    @microsecond.setter
    def microsecond(self, microsecond):
        cls = self.__class__
        raise NotImplementedError()

    @property
    def weekday(self):
        return self.datetime.isoweekday()
    
    @property
    def day_of_year(self):
        """ The day of the year for this When instant.
            
            >>> earth_day = When(year=2015, month=4, day=22, hour=5, 
            ...                  timezone='America/New_York')
            >>> earth_day.day_of_year
            112

        """    
        return self.datetime.timetuple().tm_yday

    # representations

    @property
    def timestamp(self):
        return calendar.timegm(self.utc.datetime.timetuple())
    
    posix_time = unix_time = timestamp

    def format_as_iso(self, separator='T', precision='microseconds'):
        if precision == 'seconds':
            precision_specifier = '03'
        elif precision == 'milliseconds':
            precision_specifier = '03.012'
        elif precision == 'microseconds':
            precision_specifier = '03.012345'
        specifier = '{:1776-07-04' + separator + '13:02:' + precision_specifier + '-04:00}'
        return specifier.format(self)

    @property
    def iso_format(self):
        """ Return the instant in the timezone view in ISO-8601 format.
            
            >>> earth_day = When(2015, 4, 22, timezone='utc')
            >>> earth_day.iso_format
            '2015-04-22T00:00:00.000+00:00'
        
        """
        return self.format_as_iso(precision='milliseconds')

    isoformat = iso_format

    # summarizing helpers

    @staticmethod
    def _dict_from_datetime(datetime):
        attributes = ('year', 'month', 'day', 'hour', 'minute', 
                      'second', 'microsecond')
        return {attribute: getattr(datetime, attribute) for 
                attribute in attributes}

    @property
    def _immutable_attributes_tuple(self):
        attributes = ('year', 'month', 'day', 'hour', 'minute', 
                      'second', 'microsecond')
        return tuple(getattr(self.utc, attribute) for attribute in attributes)

    _comparison_tuple = _immutable_attributes_tuple

    @property
    def _init_tuple(self):
        attributes = ('year', 'month', 'day', 'hour', 'minute', 
                      'second', 'microsecond','_timezone', 'dst')
        return tuple(getattr(self, attribute) for attribute in attributes)

    # comparison

    def __eq__(self, other):
        """ Returns equivalence against other When-like objects.
        
            >>> When(2015, 1, 1, timezone='utc') == \
                When(2015, 1, 1, timezone='utc')
            True
            >>> new_york = When(2015, 1, 1, 12, timezone='America/New_York')
            >>> los_angeles = When(2015, 1, 1, 9, timezone='America/Los_Angeles')
            >>> new_york == los_angeles
            True
        
        """
        return self._comparison_tuple == other._comparison_tuple

    def __lt__(self, other):
        """ Returns less than operator against other When-like objects.
        
            >>> When(2015, 1, 1, timezone='utc') < \
                When(2015, 1, 1, timezone='utc')
            False
            
        """
        return self._comparison_tuple < other._comparison_tuple

    def __le__(self, other):
        """ Returns less than or equal operator against When-like objects.
        
            >>> When(2015, 1, 1, timezone='utc') <= \
                When(2015, 1, 1, timezone='utc')
            True
            
        """
        return self._comparison_tuple <= other._comparison_tuple

    def __gt__(self, other):
        """ Returns greater than operator against other When-like objects.
        
            >>> When(2015, 1, 1, timezone='utc') > \
                When(2015, 12, 31, timezone='utc')
            False
            
        """
        return self._comparison_tuple > other._comparison_tuple

    def __ge__(self, other):
        """ Returns greater than or equal operator against When-like objects.
        
            >>> When(2015, 1, 1, timezone='utc') >= \
                When(2015, 1, 1, timezone='utc')
            True
            
        """
        return self._comparison_tuple >= other._comparison_tuple

    # representation

    def __str__(self):
        """ Return a string representation of the When instance.
            
            >>> str(When(2015, 1, 2, 3, 4, 5, timezone='utc'))
            '2015-01-02 03:04:05+00:00'
            
        """
        return str(self.datetime)

    def __repr__(self):
        """ Return a string that can be used to reproduce this When instance.
            
            >>> repr(When(2015, 1, 2, 3, 4, 5, 666666, timezone='utc'))
            "When(2015, 1, 2, 3, 4, 5, 666666, 'utc', False)"
            
        """
        return '{}{}'.format(self.__class__.__name__, self._init_tuple)

    def __hash__(self):
        """ Return the hash of a When instance.
        
            The unique instant represented by a When is defined unambiguously
            by a hash of the utc immutable attributes.
        
        """
        return hash(self._immutable_attributes_tuple)

    # pickle-related
    
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
            >>> str(earth_day)
            '2015-04-22 00:00:00-04:00'
            >>> earth_day.timezone == timezones['America/New_York']
            True
            
        """
        return (self.__class__, self._init_tuple, )



def now(timezone='utc'):
    """ Return a When object at this instant, with initial view set by 
        ```timezone```.
        
    """
    return When.now(timezone)


def parse(string, specifier, *args, **kwargs):
    return When.from_string(string, specifier, *args, **kwargs)
