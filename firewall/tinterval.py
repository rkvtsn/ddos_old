#
import threading

class TimeInterval(object):
    
    
    '''
    timeout - timeout in seconds
    fn - function
    '''
    def __init__(self, timeout, fn):

        self.t = None
        self.fn = fn
        self.timeout = timeout
        self._is_stoped = False
    
    
    '''
    Launch interval with init params
    '''
    def start(self):
        
        if self._is_stoped == True:
            return
        
        def func_wrapper():
        
            self.fn()
            self.start()
            #self.timeout = self.fn()
        
        self.t = threading.Timer(self.timeout, func_wrapper)
        self.t.start()
    
    
    '''
    Stop interval
    '''
    def stop(self):
        
        self._is_stoped = True
        self.t.cancel()
    

    '''
    Restart interval, reset timeout and launch
    '''
    def set_timeout(self, timeout):
        self.timeout = timeout
        self.stop()
        self._is_stoped = False
        self.start()
        