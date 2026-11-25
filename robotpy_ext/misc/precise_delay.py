from typing import Self

import hal
import wpilib
from wpiutil import sync


class NotifierDelay:
    """Synchronizes a timing loop against an alarm.

    This will delay so that the next invocation of your loop happens at
    precisely the same period, assuming that your loop does not take longer
    than the specified period.

    In simulation, each alarm remains unacknowledged until the next call to
    :meth:`wait`, so synchronous time stepping waits for the intervening loop
    work to complete. Keep the same delay across mode transitions to preserve
    this synchronization. Always free the delay when the loop exits.

    Example::

        with NotifierDelay(0.02) as delay:
            while something:
                # do things here
                delay.wait()
    """

    def __init__(self, delay_period: float) -> None:
        """:param delay_period: The period's amount of time (in seconds)."""
        self._notifier = None
        self._needs_rearm = False
        if delay_period < 0.001:
            raise ValueError("You probably don't want to delay less than 1ms!")

        # Convert the delay period to nanoseconds, as WPILib timestamps are nanoseconds
        self.delay_period = int(delay_period * 1e9)
        self._notifier = hal.create_notifier()[0]
        self._expiry_time = wpilib.RobotController.get_time() + self.delay_period
        hal.set_notifier_alarm(self._notifier, self._expiry_time, 0, True, True)

    def __del__(self):
        self.free()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.free()

    def free(self) -> None:
        """Clean up the notifier.

        Do not use this object after this method is called.
        """
        if self._notifier is not None:
            hal.destroy_notifier(self._notifier)
            self._notifier = None

    def wait(self) -> None:
        """Wait until the delay period has passed."""
        if self._notifier is None:
            return
        # Acknowledge only after the caller has finished the loop work.
        # Simulation stepping must not advance while that work is running.
        if self._needs_rearm:
            self._expiry_time += self.delay_period
            hal.set_notifier_alarm(self._notifier, self._expiry_time, 0, True, True)
        self._needs_rearm = True
        sync.wait_for_object(self._notifier)
