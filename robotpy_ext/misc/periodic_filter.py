import logging
import time


class PeriodicFilter:
    """
        Periodic Filter to help keep down clutter in the console.
        Simply add this filter to your logger and the logger will
        only print periodically.

        The logger will always print logging levels of WARNING or higher,
        unless given a different bypass level
        
        Example::
        
            class Component1:

                def setup(self):
                    # Set period to 3 seconds, set bypass_level to WARN
                    self.filter = PeriodicFilter(3, bypass_level=logging.WARN)
                    self.logger.addFilter(filter)

                def execute(self):
                    # These messages will be printed once every three seconds
                    self.logger.info('Component1 Executing')
                    self.logger.debug('Here are some values...')

                    # This message will be printed out every loop
                    self.logger.warn("Uh oh, this shouldn't have happened...")

                    self.filter.refresh() # Not needed when using magicbot framework
        
    """

    def __init__(self, period, bypass_level=logging.WARN):
        """
         :param period: Wait period (in seconds) between logs
         :param bypass_level: Lowest logging level that the filter should not catch
        """

        self._period = period
        self._loggingLoop = True
        self._last_log = -period
        self._bypass_level = bypass_level

    def filter(self, record):
        """Performs filtering action for logger"""
        return self._loggingLoop or record.levelno >= self._bypass_level

    def refresh(self):
        """Determine if the log wait period has passed"""
        now = time.monotonic()
        self._loggingLoop = False
        if now - self._last_log > self._period:
            self._loggingLoop = True
            self._last_log = now
