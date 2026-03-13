from __future__ import annotations

import commands2


class CommandRunner:
    def run(self, command: commands2.Command) -> None:
        raise NotImplementedError

    def execute(self) -> None:
        raise NotImplementedError
