#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#

from robot import MyRobot
from wpilib import autonomous

from magicbot import AutonomousStateMachine, timed_state, tunable
from components.component2 import Component2


@autonomous
class TwoSteps(AutonomousStateMachine):

    component2: Component2

    drive_speed = tunable(-1)

    @timed_state(duration=2, next_state="do_something", first=True)
    def dont_do_something(self):
        """This happens first"""

    @timed_state(duration=5)
    def do_something(self):
        """This happens second"""
        self.component2.do_something()
