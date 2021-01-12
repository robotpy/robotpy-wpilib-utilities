import hal
import time
import warnings
import wpilib


class PreciseDelay:
    """
    Used to synchronize a timing loop. Will delay precisely so that
    the next invocation of your loop happens at the same period, as long
    as your code does not run longer than the length of the delay.

    Our experience has shown that 25ms is a good loop period.

    Usage::

        delay = PreciseDelay(time_to_delay)

        while something:
            # do things here
            delay.wait()

    .. deprecated:: 2019
       PreciseDelay is terribly inefficient. Use :class:`NotifierDelay` instead.
    """

    def __init__(self, delay_period):
        """
        :param delay_period: The amount of time (in seconds) to do a delay
        :type delay_period: float
        """
        warnings.warn(
            "PreciseDelay is deprecated, use NotifierDelay instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )

        # The WPILib sleep/etc functions are slightly less stable as
        # they have more overhead, so only use them in simulation mode
        if wpilib.RobotBase.isSimulation():

            self.delay = wpilib.Timer.delay
            self.get_now = wpilib.Timer.getFPGATimestamp

            # Test to see if we're in a unit test, and switch the wait function
            # to run more efficiently -- otherwise full tests are dog slow
            try:
                import pyfrc.config

                if pyfrc.config.mode in ("test", "upload"):
                    self.wait = self._wait_unit_tests
            except:
                pass

        else:
            self.delay = time.sleep
            self.get_now = time.monotonic

        self.delay_period = float(delay_period)
        if self.delay_period < 0.001:
            raise ValueError("You probably don't want to delay less than 1ms!")

        self.next_delay = self.get_now() + self.delay_period

    def wait(self):
        """Waits until the delay period has passed"""

        # optimization -- avoid local lookups
        delay = self.delay
        get_now = self.get_now
        next_delay = self.next_delay

        while True:
            # we must *always* yield here, so other things can run
            delay(0.0002)

            if next_delay < get_now():
                break

        self.next_delay += self.delay_period

    def _wait_unit_tests(self):

        # Not optimized -- just need the unit tests to run fast
        # - TODO: should we just always use this in simulated mode?

        wpilib.Timer.delay(self.delay_period)

    def __enter__(self) -> "PreciseDelay":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class NotifierDelay:
    """Synchronizes a timing loop against interrupts from the FPGA.

    This will delay so that the next invocation of your loop happens at
    precisely the same period, assuming that your loop does not take longer
    than the specified period.

    Example::

        with NotifierDelay(0.02) as delay:
            while something:
                # do things here
                delay.wait()
    """

    def __init__(self, delay_period: float) -> None:
        """:param delay_period: The period's amount of time (in seconds)."""
        if delay_period < 0.001:
            raise ValueError("You probably don't want to delay less than 1ms!")

        # Convert the delay period to microseconds, as FPGA timestamps are microseconds
        self.delay_period = int(delay_period * 1e6)
        self._notifier = hal.initializeNotifier()[0]
        self._expiry_time = wpilib.RobotController.getFPGATime() + self.delay_period
        self._update_alarm(self._notifier)

        # wpilib.Resource._add_global_resource(self)

    def __del__(self):
        self.free()

    def __enter__(self) -> "NotifierDelay":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.free()

    def free(self) -> None:
        """Clean up the notifier.

        Do not use this object after this method is called.
        """
        handle = self._notifier
        if handle is None:
            return
        hal.stopNotifier(handle)
        hal.cleanNotifier(handle)
        self._notifier = None

    def wait(self) -> None:
        """Wait until the delay period has passed."""
        handle = self._notifier
        if handle is None:
            return
        hal.waitForNotifierAlarm(handle)
        self._expiry_time += self.delay_period
        self._update_alarm(handle)

    def _update_alarm(self, handle) -> None:
        hal.updateNotifierAlarm(handle, self._expiry_time)
