import wpilib
import logging
from typing import List, Tuple

logger = logging.getLogger("simple_watchdog")

__all__ = ["SimpleWatchdog"]


class SimpleWatchdog:
    """A class that's a wrapper around a watchdog timer.

    When the timer expires, a message is printed to the console and an optional user-provided
    callback is invoked.

    The watchdog is initialized disabled, so the user needs to call enable() before use.

    .. note:: This is a simpler replacement for the :class:`wpilib.Watchdog`,
              and should function mostly the same (except that this watchdog will
              not detect infinite loops).

    .. warning:: This watchdog is not threadsafe

    """

    # Used for timeout print rate-limiting
    kMinPrintPeriod = 1000000  # us

    def __init__(self, timeout: float):
        """Watchdog constructor.

        :param timeout: The watchdog's timeout in seconds with microsecond resolution.
        """
        self._get_time = wpilib.RobotController.getFPGATime

        self._startTime = 0  # us
        self._timeout = int(timeout * 1e6)  # us
        self._expirationTime = 0  # us
        self._lastTimeoutPrintTime = 0  # us
        self._lastEpochsPrintTime = 0  # us
        self._epochs: List[Tuple[str, int]] = []

    def getTime(self) -> float:
        """Returns the time in seconds since the watchdog was last fed."""
        return (self._get_time() - self._startTime) / 1e6

    def setTimeout(self, timeout: float) -> None:
        """Sets the watchdog's timeout.

        :param timeout: The watchdog's timeout in seconds with microsecond
                        resolution.
        """
        self._epochs.clear()
        timeout = int(timeout * 1e6)  # us
        self._timeout = timeout
        self._startTime = self._get_time()
        self._expirationTime = self._startTime + timeout

    def getTimeout(self) -> float:
        """Returns the watchdog's timeout in seconds."""
        return self._timeout / 1e6

    def isExpired(self) -> bool:
        """Returns true if the watchdog timer has expired."""
        return self._get_time() > self._expirationTime

    def addEpoch(self, epochName: str) -> None:
        """
        Adds time since last epoch to the list printed by printEpochs().

        Epochs are a way to partition the time elapsed so that when
        overruns occur, one can determine which parts of an operation
        consumed the most time.

        :param epochName: The name to associate with the epoch.
        """
        self._epochs.append((epochName, self._get_time()))

    def printIfExpired(self) -> None:
        """Prints list of epochs added so far and their times."""
        now = self._get_time()
        if (
            now > self._expirationTime
            and now - self._lastEpochsPrintTime > self.kMinPrintPeriod
        ):
            log = logger.info
            self._lastEpochsPrintTime = now
            prev = self._startTime
            log("Watchdog not fed after %.6fs", (now - prev) / 1e6)
            for key, value in self._epochs:
                log("\t%s: %.6fs", key, (value - prev) / 1e6)
                prev = value

    def reset(self) -> None:
        """Resets the watchdog timer.

        This also enables the timer if it was previously disabled.
        """
        self.enable()

    def enable(self) -> None:
        """Enables the watchdog timer."""
        self._epochs.clear()
        self._startTime = self._get_time()
        self._expirationTime = self._startTime + self._timeout

    def disable(self) -> None:
        """Disables the watchdog timer."""
        # .. this doesn't do anything
