# standard libraries
import doctest
# third party libraries
pass
# first party libraries
import when


doctest.testmod(when.when)
doctest.testmod(when._substitutions)


#when.When.from_string('2015-03-03 02:58:59', '1776-07-04 01:02:03', timezone='utc')