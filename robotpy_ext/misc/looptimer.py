import math
import wpilib

_getFPGATimestamp = wpilib.Timer.getFPGATimestamp


class LoopTimer:
    """
    A utility class that measures the number of loops that a robot program
    executes, and computes the min/max/average period for loops in the last
    second.

    Example usage::

        class Robot(wpilib.IterativeRobot):

            def teleopInit(self):
                self.loop_timer = LoopTimer(self.logger)

            def teleopPeriodic(self):
                self.loop_timer.measure()

    Mainly intended for debugging purposes to measure how much lag.
    """

    def __init__(self, logger):
        self.logger = logger
        self.timer = wpilib.Timer()
        self.timer.start()

        self.reset()

    def reset(self):
        self.timer.reset()

        self.start = self.last = _getFPGATimestamp()
        self.min_time = math.inf
        self.max_time = -1
        self.loops = 0

    def measure(self):
        """
        Computes loop performance information and periodically dumps it to
        the info logger.
        """

        # compute min/max/count
        now = _getFPGATimestamp()
        diff = now - self.last
        self.min_time = min(self.min_time, diff)
        self.max_time = max(self.max_time, diff)

        self.loops += 1
        self.last = now

        if self.timer.hasPeriodPassed(1):
            self.logger.info(
                "Loops: %d; min: %.3f; max: %.3f; period: %.3f; avg: %.3f",
                self.loops,
                self.min_time,
                self.max_time,
                now - self.start,
                (now - self.start) / self.loops,
            )

            self.min_time = math.inf
            self.max_time = -1
            self.start = now
            self.loops = 0
