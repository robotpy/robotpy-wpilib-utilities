import logging
import wpilib


class PeriodicFilter:
    """
        Periodic Filter to help keep down clutter in the console.
        Simply add this filter to your logger and the logger will
        only print periodically.

        The logger will always print logging levels of WARNING or higher
    """

    def __init__(self, period, bypassLevel=logging.WARN):
        '''
         :param period: Wait period (in seconds) between logs
        '''

        self.period = period
        self.loggingLoop = True
        self._last_log = -period
        self.bypassLevel = bypassLevel

    def filter(self, record):
        """Performs filtering action for logger"""
        self._refresh_logger()
        return self.parent.loggingLoop or record.levelno >= self.bypassLevel

    def _refresh_logger(self):
        """Determine if the log wait period has passed"""
        now = wpilib.Timer.getFPGATimestamp()
        self.loggingLoop = False
        if now - self.__last_log > self.logging_interval:
            self.loggingLoop = True
            self.__last_log = now
