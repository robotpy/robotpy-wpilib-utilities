from __future__ import annotations

from typing import Callable

import commands2


class CommandRunner:
    """
    A MagicBot component that executes ``commands2.Command`` instances using
    keep-alive semantics.

    Call :meth:`run` to start a stored command instance. Once started, a
    command continues running on each later loop until it reports finished.

    Multiple different commands may be active concurrently. Repeated
    :meth:`run` calls for the same command instance in a single loop are
    deduplicated.

    This component intentionally does not expose or depend on
    ``commands2.CommandScheduler``.
    """

    robot: object

    def __init__(self) -> None:
        self._requested: dict[commands2.Command, None] = {}
        self._active: dict[commands2.Command, None] = {}

    def run(self, command: commands2.Command) -> None:
        """
        Request that a stored command instance start running.
        """
        self._requested.setdefault(command, None)

    def _discard(self, command: commands2.Command) -> None:
        self._requested.pop(command, None)
        self._active.pop(command, None)

    def _call(self, command: commands2.Command, func: Callable[[], object]) -> bool:
        try:
            func()
        except Exception:
            self._discard(command)
            self.robot.onException()
            return False
        return True

    def execute(self) -> None:
        new_commands = [
            command for command in self._requested if command not in self._active
        ]
        for command in new_commands:
            if self._call(command, command.initialize):
                self._active[command] = None

        commands_to_execute = [
            command for command in self._requested if command in self._active
        ]
        commands_to_execute.extend(
            command for command in self._active if command not in self._requested
        )

        finished: list[commands2.Command] = []
        for command in commands_to_execute:
            if not self._call(command, command.execute):
                continue
            if command.isFinished():
                if self._call(command, lambda command=command: command.end(False)):
                    finished.append(command)

        for command in finished:
            self._active.pop(command, None)

        self._requested.clear()
