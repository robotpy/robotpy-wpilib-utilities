#!/usr/bin/env python3
#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#

import wpilib
from components.component1 import Component1
from components.component2 import Component2

from magicbot import MagicRobot


class Talon(wpilib.PWMMotorController):
    """PWM Talon configuration (pulse widths in microseconds)."""

    def __init__(self, channel):
        super().__init__(channel)
        self._set_bounds(2037, 1539, 1513, 1487, 989)
        self.set_throttle(0)


class MyRobot(MagicRobot):
    #
    # Define components here
    #

    component1: Component1
    component2: Component2

    # You can even pass constants to components
    SOME_CONSTANT = 1

    def create_objects(self):
        """Initialize all wpilib motors & sensors"""

        # TODO: create button example here

        self.component1_motor = Talon(1)
        self.some_motor = Talon(2)

        self.joystick = wpilib.Joystick(0)
