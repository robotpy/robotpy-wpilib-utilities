from magicbot import will_reset_to
from magicbot.commands import CommandRunner

from external_auto import DriveForward


class Drive:
    """Hardware-free drivetrain: integrate speed (m/s) into distance (m)."""

    speed = will_reset_to(0.0)

    def __init__(self):
        self.distance = 0.0
        self.output = 0.0

    def set_speed(self, speed):
        self.speed = speed

    def execute(self):
        self.output = self.speed
        self.distance += self.output * 0.02

    def on_disable(self):
        self.output = 0.0


class AutoCommands:
    """Adapt a library's command to MagicBot's component lifecycle."""

    runner: CommandRunner
    drive: Drive

    def setup(self):
        # Construct once after injection. A library-generated autonomous command
        # could be stored here instead, with callbacks into our drivetrain.
        self.command = DriveForward(self.drive.set_speed)
        self.start_requested = False

    def start(self):
        self.start_requested = True

    def stop(self):
        self.start_requested = False
        self.runner.cancel(self.command)

    def execute(self):
        if self.start_requested:
            self.start_requested = False
            self.runner.run(self.command)
        # No further requests are needed: the runner drives the command's
        # lifecycle until is_finished() returns True.
