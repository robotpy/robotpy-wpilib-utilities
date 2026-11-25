from __future__ import annotations

from collections.abc import Callable

import commands2
import wpilib


class CommandRunner:
    """
    A MagicBot component that executes ``commands2.Command`` instances using
    run-to-completion semantics.

    Call :meth:`run` to start a stored command instance. Once started, a
    command continues running on each later loop until it reports finished.

    Multiple different commands may be active concurrently. Repeated
    :meth:`run` calls for the same command instance in a single loop are
    deduplicated.

    This component intentionally does not expose or depend on
    ``commands2.CommandScheduler``.
    """

    error_report_interval = 0.5

    def __init__(self) -> None:
        self._last_error_report = -10.0
        self._requested: dict[commands2.Command, None] = {}
        self._processing: dict[commands2.Command, None] = {}
        self._active: dict[commands2.Command, None] = {}

    def run(self, command: commands2.Command) -> None:
        """
        Request that a stored command instance start running.

        Requests made by lifecycle callbacks are deferred to the next execute
        loop. Requests for an already active command do not initialize it again.
        """
        self._requested.setdefault(command, None)

    def cancel(self, command: commands2.Command) -> None:
        """Cancel a pending or active command.

        Active commands receive ``end(True)``. Pending commands that have not
        initialized are simply discarded. Cancelling an idle command is a no-op.
        """
        active = command in self._active
        self._discard(command)
        if active:
            self._call(command, lambda: command.end(True))

    def on_disable(self) -> None:
        """Interrupt all active commands and discard all pending requests.

        Unlike CommandScheduler, this runner never runs commands while disabled.
        """
        commands = list(self._active)
        self._active.clear()
        self._requested.clear()
        self._processing.clear()
        error = None
        try:
            for command in commands:
                try:
                    self._call(command, lambda: command.end(True))
                except Exception as exc:
                    if error is None:
                        error = exc
        finally:
            # Even end() callbacks must not leave work queued for re-enable.
            self._active.clear()
            self._requested.clear()
            self._processing.clear()
        if error is not None:
            raise error

    def _discard(self, command: commands2.Command) -> None:
        self._requested.pop(command, None)
        self._processing.pop(command, None)
        self._active.pop(command, None)

    def _call(self, command: commands2.Command, func: Callable[[], object]) -> object:
        try:
            return func()
        except Exception:
            self._discard(command)
            if not wpilib.RobotState.is_fms_attached():
                raise

            now = wpilib.Timer.get_timestamp()
            try:
                if now - self._last_error_report > self.error_report_interval:
                    wpilib.report_error("Unexpected exception", True)
            except Exception:
                pass  # Reporting failures must not stop the robot during a match.
            self._last_error_report = now
            return None

    def execute(self) -> None:
        self._processing, self._requested = self._requested, {}
        try:
            new_commands = [
                command for command in self._processing if command not in self._active
            ]
            for command in new_commands:
                if command not in self._processing:
                    continue
                self._active[command] = None
                self._call(command, command.initialize)

            commands_to_execute = [
                command for command in self._processing if command in self._active
            ]
            commands_to_execute.extend(
                command for command in self._active if command not in self._processing
            )

            for command in commands_to_execute:
                if command not in self._active:
                    continue
                self._call(command, command.execute)
                if command not in self._active:
                    continue
                finished = self._call(command, command.is_finished)
                if command in self._active and finished:
                    self._active.pop(command, None)
                    self._call(command, lambda command=command: command.end(False))
        finally:
            self._processing.clear()
