# standard libraries
import datetime
# third party libraries
pass
# first party libraries
from . import substitutions


__all__ = ('While', )


class While(object):
    """ An alternative to ```datetime.timedelta``` with intuitive attributes.

        pass
    """
    
    conversions = {} # to seconds
    conversions['microseconds'] = 1e-6
    conversions['milliseconds'] = 1e-3
    conversions['seconds'] = 1
    conversions['minutes'] = 60
    conversions['hours'] = 3600
    conversions['days'] = 24*conversions['hours']
    conversions['weeks'] = 7*conversions['days']
    
    def __init__(self, days=0, hours=0, minutes=0, seconds=0, milliseconds=0, 
                 microseconds=0):
        self._seconds = days*self.conversions['days'] + \
                        hours*self.conversions['hours'] + \
                        minutes*self.conversions['minutes'] + \
                        seconds*self.conversions['seconds'] + \
                        milliseconds*self.conversions['milliseconds'] + \
                        microseconds*self.conversions['microseconds']

    @classmethod
    def from_timedelta(cls, timedelta):
        return cls(seconds=timedelta.total_seconds())

    def to(self, *units):
        pass

    @property
    def timedelta(self):
        return datetime.timedelta(seconds=self.seconds)
    
    def __format__(self, specifier):
        pass
   
    """
    @staticmethod
    def _tensify(seconds, description):
        if seconds < 0:
            return '{} ago'.format(description)
        elif seconds > 0:
            return 'in {}'.format(description)
        else:
            return description
    
    def humanize(self, tensify=True, precise=False):
        if self.seconds == 0:
            return 'now'
        elif 0 < abs(self.seconds) <= 10:
            description = 'a few seconds'
        elif 10 < abs(self.seconds) <= 50:
            if precise:
                description = '{} seconds'.format(round(self.seconds))
            else:
                description = 'about {} seconds'.format(round(self.seconds, -1))
        elif 50 < abs(self.seconds) <= 80:
            pass
        #
        if tensify:
            return self._tensify(self.seconds, description)
        else:
            return description
    """
    
    def __getattr__(self, name):
        try:
            return self._seconds/self.conversions[name]
        except KeyError:
            raise AttributeError('Attribute {} does not exist.'.format(name))
    
    def __add__(self, other):
        return self.__class__(seconds=(self.seconds + other.seconds))

    def __sub__(self, other):
        return self.__class__(seconds=(self.seconds - other.seconds))

    def __div__(self, other):
        return self.__class__(seconds=self.seconds/other)

    def __mul__(self, other):
        return self.__class__(seconds=self.seconds*other)
    
    def __abs__(self):
        return self.__class__(seconds=abs(self.seconds))

