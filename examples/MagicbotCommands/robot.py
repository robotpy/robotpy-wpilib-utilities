#!/usr/bin/env python3

from magicbot import MagicRobot
from magicbot.commands import CommandRunner

from components import AutoCommands, Drive


class MyRobot(MagicRobot):
    # Execution order matters: request commands, execute them, then apply their
    # drivetrain outputs in the same loop.
    auto_commands: AutoCommands
    runner: CommandRunner
    drive: Drive

    def create_objects(self):
        pass  # This example needs no physical hardware.

    def teleop_periodic(self):
        pass
