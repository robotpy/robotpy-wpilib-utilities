import hal
import wpilib


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
