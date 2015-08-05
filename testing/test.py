# standard libraries
import doctest
# third party libraries
pass
# first party libraries
import when


doctest.testmod(when.when)

print(when.when.now('America/New_York').datetime.utcoffset())
print(when.when.now('America/New_York').utcoffset)