# standard libraries
import time
# third party libraries
pass
# first party libraries
from . import when


__all__ = ('sleep', 'Timer', 'tic', 'toc', )


def sleep(seconds):
    time.sleep(seconds)

    
class Timer(object):
    
    def __init__(self):
        self.tic()
        
    def tic(self):
        self.awhile = None
        self.stopped = None
        self.started = when.When.now()
        
    def toc(self):
        self.stopped = when.When.now()
        self.awhile = self.stopped - self.started
        return self.awhile


timer = Timer()


def tic():
    timer.tic()

    
def toc():
    return timer.toc()
