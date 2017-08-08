import logging
import time


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
         :param bypassLevel: Lowest logging level that the filter should ignore
        '''

        self._period = period
        self._loggingLoop = True
        self._last_log = -period
        self._bypassLevel = bypassLevel

    def filter(self, record):
        """Performs filtering action for logger"""
        self._refresh_logger()
        return self._loggingLoop or record.levelno >= self._bypassLevel

    def _refresh_logger(self):
        """Determine if the log wait period has passed"""
        now = time.monotonic()
        self._loggingLoop = False
        if now - self._last_log > self._period:
            self._loggingLoop = True
            self._last_log = now
