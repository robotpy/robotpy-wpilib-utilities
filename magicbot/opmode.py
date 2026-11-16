import wpilib

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from magicbot import MagicRobot


class PeriodicOpMode(wpilib.PeriodicOpMode):
    def __init__(self, robot: MagicRobot):
        super().__init__()
        self.robot = robot
