# standard libraries
import unittest
import doctest
# third party libraries
pass
# first party libraries
import when

now = when.When.now()

doctest.testmod(when.when)