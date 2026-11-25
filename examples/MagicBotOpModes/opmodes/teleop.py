#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#

import wpilib
from robot import MyRobot
from wpilib import PeriodicOpMode, teleop

from components.component2 import Component2


@teleop
class NormalOperation(PeriodicOpMode):

    joystick: wpilib.Joystick
    component2: Component2

    def periodic(self) -> None:
        if self.joystick.get_trigger():
            self.component2.do_something()
