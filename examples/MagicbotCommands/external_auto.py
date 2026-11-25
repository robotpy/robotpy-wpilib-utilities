"""A stand-in for an autonomous command supplied by an external library.

This module knows nothing about MagicBot. A real library could use odometry
and a trajectory instead of simply driving forward for a fixed duration.
"""

from collections.abc import Callable
from typing import override

import commands2
import wpilib


class DriveForward(commands2.Command):
    def __init__(self, set_speed: Callable[[float], None]):
        super().__init__()
        self.set_speed = set_speed
        self.timer = wpilib.Timer()

    @override
    def initialize(self):
        self.timer.restart()

    @override
    def execute(self):
        self.set_speed(0.5)

    @override
    def is_finished(self):
        return self.timer.has_elapsed(1.0)

    @override
    def end(self, interrupted):
        self.set_speed(0.0)
        self.timer.stop()
