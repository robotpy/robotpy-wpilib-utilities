from __future__ import annotations

import commands2


class CommandRunner:
    def __init__(self) -> None:
        self._requested: set[commands2.Command] = set()
        self._active: set[commands2.Command] = set()

    def run(self, command: commands2.Command) -> None:
        self._requested.add(command)

    def execute(self) -> None:
        stale = [
            command
            for command in self._active
            if command not in self._requested
            and command.getInterruptionBehavior()
            != commands2.Command.InterruptionBehavior.kCancelIncoming
        ]
        for command in stale:
            command.end(True)
            self._active.remove(command)

        new_commands = [
            command for command in self._requested if command not in self._active
        ]
        for command in new_commands:
            command.initialize()
            self._active.add(command)

        finished: list[commands2.Command] = []
        for command in list(self._active):
            command.execute()
            if command.isFinished():
                command.end(False)
                finished.append(command)

        for command in finished:
            self._active.remove(command)

        self._requested.clear()
