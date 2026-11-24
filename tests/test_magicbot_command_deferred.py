import pytest

from magicbot.commands import CommandRunner
from test_magicbot_commands import RecordingCommand


@pytest.mark.parametrize("stage", ["initialize", "execute", "is_finished", "end"])
@pytest.mark.parametrize("duplicates", [1, 3])
def test_callback_requests_deferred(stage, duplicates):
    runner = CommandRunner()
    first = RecordingCommand(finished_after=1)
    following = [RecordingCommand(), RecordingCommand()]
    events = []
    original = getattr(first, stage)

    def callback(*args):
        for _ in range(duplicates):
            for command in following:
                runner.run(command)
        return original(*args)

    setattr(first, stage, callback)
    for i, command in enumerate(following):
        original_initialize = command.initialize

        def initialize(i=i, original_initialize=original_initialize):
            events.append(i)
            original_initialize()

        command.initialize = initialize
    runner.run(first)
    runner.execute()
    assert events == []
    runner.execute()
    assert events == [0, 1]
    assert [c.execute_calls for c in following] == [1, 1]


def test_cancel_snapshotted_pending():
    runner = CommandRunner()
    first, pending = RecordingCommand(), RecordingCommand()
    first.initialize = lambda: runner.cancel(pending)
    runner.run(first)
    runner.run(pending)
    runner.execute()
    assert pending.initialize_calls == pending.execute_calls == 0


@pytest.mark.parametrize("disable", [False, True])
def test_clear_deferred(disable):
    runner = CommandRunner()
    first, pending = RecordingCommand(), RecordingCommand()
    first.initialize = lambda: runner.run(pending)
    first.end = lambda interrupted: runner.run(pending)
    runner.run(first)
    runner.execute()
    if disable:
        runner.on_disable()
        assert not runner._active
    else:
        runner.cancel(pending)
    runner.execute()
    assert pending.initialize_calls == pending.execute_calls == 0


def test_active_duplicate_does_not_reinitialize():
    runner = CommandRunner()
    command = RecordingCommand()
    command.execute = lambda: runner.run(command)
    runner.run(command)
    runner.execute()
    runner.execute()
    assert command.initialize_calls == 1


def test_end_can_reschedule_finished_command():
    runner = CommandRunner()
    command = RecordingCommand(finished_after=1)
    command.end = lambda interrupted: runner.run(command)
    runner.run(command)
    runner.execute()
    assert command.initialize_calls == 1
    runner.execute()
    assert command.initialize_calls == 2
