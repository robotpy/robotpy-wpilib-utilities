from __future__ import annotations

from typing import Callable

import commands2


class CommandRunner:
    """
    A MagicBot component that executes ``commands2.Command`` instances using
    keep-alive semantics.

    Call :meth:`run` each loop that a stored command instance should remain
    active. Commands that are not re-requested on a later loop are interrupted
    automatically if they are interruptible.

    Multiple different commands may be active concurrently. Repeated
    :meth:`run` calls for the same command instance in a single loop are
    deduplicated.

    This component intentionally does not expose or depend on
    ``commands2.CommandScheduler``.
    """

    robot: object

    def __init__(self) -> None:
        self._requested: dict[commands2.Command, None] = {}
        self._active: set[commands2.Command] = set()

    def run(self, command: commands2.Command) -> None:
        """
        Request that a stored command instance remain active for the current
        robot loop.
        """
        self._requested.setdefault(command, None)

    def _discard(self, command: commands2.Command) -> None:
        self._requested.pop(command, None)
        self._active.discard(command)

    def _call(self, command: commands2.Command, func: Callable[[], object]) -> bool:
        try:
            func()
        except Exception:
            self._discard(command)
            self.robot.onException()
            return False
        return True

    def execute(self) -> None:
        stale = [
            command
            for command in self._active
            if command not in self._requested
            and command.getInterruptionBehavior()
            != commands2.Command.InterruptionBehavior.kCancelIncoming
        ]
        for command in stale:
            if self._call(command, lambda command=command: command.end(True)):
                self._active.remove(command)

        new_commands = [
            command for command in self._requested if command not in self._active
        ]
        for command in new_commands:
            if self._call(command, command.initialize):
                self._active.add(command)

        finished: list[commands2.Command] = []
        for command in list(self._requested):
            if command not in self._active:
                continue
            if not self._call(command, command.execute):
                continue
            if command.isFinished():
                if self._call(command, lambda command=command: command.end(False)):
                    finished.append(command)

        for command in finished:
            self._active.remove(command)

        self._requested.clear()
