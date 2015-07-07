# standard libraries
import unittest
# third party libraries
pass
# first party libraries
import when

"""
sometime = when.When(2015, 1, 2, 1, 1, timezone='America/New_York')
print(sometime)

sometime = when.now(timezone='America/New_York')
print(sometime)
"""

import datetime

naive = datetime.datetime.utcnow()
kwargs = when.When.datetime_to_dict(naive)
kwargs['timezone'] = 'utc'
now = when.When(**kwargs)
print(now, now.timezone)

now.timezone = 'America/New_York'
print(now, now.timezone)
print(now.hour)
#print(now._hour)
#now._hour = 10
#print(now._hour)

"""
sometime = when.now()
print(sometime)

sometime = when.now('America/New_York')
"""