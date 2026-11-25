#!/usr/bin/env python3
#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#

import wpilib
from examples.MagicBotOpModes.components.component1 import Component1
from examples.MagicBotOpModes.components.component2 import Component2

from magicbot import MagicRobot


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

        self.component1_motor = wpilib.PWMMotorController(1)
        self.some_motor = wpilib.PWMMotorController(2)

        self.joystick = wpilib.Joystick(0)
