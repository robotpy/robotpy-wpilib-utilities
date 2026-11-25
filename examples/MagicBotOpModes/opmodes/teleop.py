#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#

import wpilib
from robot import MyRobot
from wpilib import PeriodicOpMode, teleop


@teleop
class NormalOperation(PeriodicOpMode):
    robot: MyRobot

    def __init__(self, robot: MyRobot) -> None:
        super().__init__()
        self.robot = robot

    def periodic(self) -> None:
        if self.robot.joystick.get_trigger():
            self.robot.component2.do_something()
