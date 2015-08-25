# standard libraries
import re
# third party libraries
pass
# first party libraries
pass


class Substitutor(object):
    """ Performs efficient one-pass multiple string substitution.
    
        >>> string = 'foo is bar, and bar is foo'
        >>> substitutions = {'foo': 'bar', 'bar': 'foo', 'and': 'or'}
        >>> substitutor = Substitutor(substitutions)
        >>> substitutor(string)
        'bar is foo, or foo is bar'
        
    """
    def __init__(self, substitutions):
        self._substitutions = substitutions
        tokens_to_replace = sorted(substitutions, key=lambda key: (len(key), key), reverse=True)
        self._regex = re.compile('|'.join(re.escape(token) for token in tokens_to_replace))
    
    def _lookup(self, match):
        return self._substitutions[match.group(0)]
    
    def __call__(self, string):
        return self._regex.sub(self._lookup, string)


def in_string(string, substitutions):
    """ Performs efficient one-pass multiple string substitution.
        
        Simple wrapper around StringSubstitutor (doesn't cache substitution 
        regex).
        
    """
    substitutor = Substitutor(substitutions)
    return substitutor(string)
