import logging

class PeriodicFilter:
    def __init__(self, parent):
        '''
        :type parent: Object
        '''
        
        self.parent = parent
        
    def filter(self, record):
        return self.parent.loggingLoop or record.levelno > logging.INFO