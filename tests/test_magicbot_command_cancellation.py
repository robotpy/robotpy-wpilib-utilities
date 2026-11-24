from unittest.mock import Mock

import pytest

from magicbot.commands import CommandRunner
from test_magicbot_commands import RecordingCommand


def test_cancel_pending_and_idle():
    runner = CommandRunner()
    command = RecordingCommand()
    runner.run(command)
    runner.cancel(command)
    runner.cancel(command)
    runner.execute()
    assert command.initialize_calls == 0
    assert command.end_calls == []


def test_cancel_active_and_restart():
    runner = CommandRunner()
    command = RecordingCommand()
    runner.run(command)
    runner.execute()
    runner.cancel(command)
    runner.cancel(command)
    runner.execute()
    assert command.execute_calls == 1
    assert command.end_calls == [True]
    runner.run(command)
    runner.execute()
    assert command.initialize_calls == 2


def test_disable_clears_active_and_pending():
    runner = CommandRunner()
    active = RecordingCommand()
    pending = RecordingCommand()
    runner.run(active)
    runner.execute()
    runner.run(pending)
    runner.on_disable()
    runner.on_disable()
    runner.execute()
    assert active.end_calls == [True]
    assert active.execute_calls == 1
    assert pending.initialize_calls == 0
    assert pending.end_calls == []


def test_disable_cleans_up_even_if_end_raises():
    runner = CommandRunner()
    first, second = RecordingCommand(), RecordingCommand()
    first.end = Mock(side_effect=RuntimeError("end failed"))
    runner.run(first)
    runner.run(second)
    runner.execute()
    with pytest.raises(RuntimeError, match="end failed"):
        runner.on_disable()
    assert second.end_calls == [True]
    assert not runner._active
    assert not runner._requested


def test_cancel_during_execute():
    runner = CommandRunner()
    first, second = RecordingCommand(), RecordingCommand()
    first.execute = lambda: (runner.cancel(first), runner.cancel(second))
    runner.run(first)
    runner.run(second)
    runner.execute()
    assert first.end_calls == [True]
    assert second.end_calls == [True]
    assert second.execute_calls == 0
