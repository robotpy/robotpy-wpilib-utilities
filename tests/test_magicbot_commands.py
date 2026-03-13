from unittest.mock import Mock

import commands2
import magicbot
import magicbot.commands


class RecordingCommand(commands2.Command):
    def __init__(self, *, finished_after: int | None = None) -> None:
        super().__init__()
        self.finished_after = finished_after
        self.initialize_calls = 0
        self.execute_calls = 0
        self.end_calls: list[bool] = []

    def initialize(self):
        self.initialize_calls += 1

    def execute(self):
        self.execute_calls += 1

    def isFinished(self) -> bool:
        return (
            self.finished_after is not None
            and self.execute_calls >= self.finished_after
        )

    def end(self, interrupted: bool):
        self.end_calls.append(interrupted)


class OrderedRecordingCommand(RecordingCommand):
    def __init__(
        self, name: str, events: list[tuple[str, str]], *, hash_value: int
    ) -> None:
        super().__init__()
        self.name = name
        self.events = events
        self.hash_value = hash_value

    def __hash__(self) -> int:
        return self.hash_value

    def initialize(self):
        super().initialize()
        self.events.append(("initialize", self.name))

    def execute(self):
        super().execute()
        self.events.append(("execute", self.name))


class RaiseOnInitialize(commands2.Command):
    def initialize(self):
        raise RuntimeError("initialize boom")


class RaiseOnExecute(commands2.Command):
    def execute(self):
        raise RuntimeError("execute boom")


class RaiseOnEnd(commands2.Command):
    def __init__(self):
        super().__init__()
        self.executed = False

    def execute(self):
        self.executed = True

    def isFinished(self) -> bool:
        return self.executed

    def end(self, interrupted: bool):
        raise RuntimeError("end boom")


class RecordingRobot(magicbot.MagicRobot):
    def createObjects(self):
        pass

    def onException(self, forceReport: bool = False) -> None:
        self.on_exception_calls += 1


class UsesCommand:
    cmd: "magicbot.commands.CommandRunner"

    def setup(self):
        self.command = RecordingCommand()
        self.should_run = False

    def execute(self):
        if self.should_run:
            self.cmd.run(self.command)


class AlsoUsesCommand:
    cmd: "magicbot.commands.CommandRunner"

    def setup(self):
        self.command = RecordingCommand()
        self.should_run = False

    def execute(self):
        if self.should_run:
            self.cmd.run(self.command)


class ComponentRobot(RecordingRobot):
    cmd: "magicbot.commands.CommandRunner"
    first: UsesCommand
    second: AlsoUsesCommand

    def createObjects(self):
        self.on_exception_calls = 0
        self._automodes = Mock()
        self._automodes.modes = {}


def make_runner():
    robot = RecordingRobot()
    robot.on_exception_calls = 0
    runner = magicbot.commands.CommandRunner()
    runner.robot = robot
    return robot, runner


def make_component_robot() -> ComponentRobot:
    robot = ComponentRobot()
    robot.createObjects()
    robot._create_components()
    return robot


def test_command_runner_initializes_executes_and_finishes_once():
    _, runner = make_runner()
    command = RecordingCommand(finished_after=2)

    runner.run(command)
    runner.execute()

    assert command.initialize_calls == 1
    assert command.execute_calls == 1
    assert command.end_calls == []

    runner.run(command)
    runner.execute()

    assert command.initialize_calls == 1
    assert command.execute_calls == 2
    assert command.end_calls == [False]


def test_command_runner_keeps_alive_requested_command():
    _, runner = make_runner()
    command = RecordingCommand()

    runner.run(command)
    runner.execute()
    runner.run(command)
    runner.execute()

    assert command.initialize_calls == 1
    assert command.execute_calls == 2
    assert command.end_calls == []


def test_command_runner_keeps_running_until_finished_without_run_call():
    _, runner = make_runner()
    command = RecordingCommand(finished_after=2)

    runner.run(command)
    runner.execute()
    runner.execute()

    assert command.initialize_calls == 1
    assert command.execute_calls == 2
    assert command.end_calls == [False]


def test_command_runner_deduplicates_same_command_requested_twice():
    _, runner = make_runner()
    command = RecordingCommand()

    runner.run(command)
    runner.run(command)
    runner.execute()

    assert command.initialize_calls == 1
    assert command.execute_calls == 1
    assert command.end_calls == []


def test_command_runner_executes_multiple_commands_concurrently():
    _, runner = make_runner()
    first = RecordingCommand()
    second = RecordingCommand()

    runner.run(first)
    runner.run(second)
    runner.execute()

    assert first.initialize_calls == 1
    assert first.execute_calls == 1
    assert second.initialize_calls == 1
    assert second.execute_calls == 1


def test_command_runner_executes_commands_in_run_call_order():
    _, runner = make_runner()
    events: list[tuple[str, str]] = []
    first = OrderedRecordingCommand("first", events, hash_value=1)
    second = OrderedRecordingCommand("second", events, hash_value=8)

    runner.run(first)
    runner.run(second)
    runner.execute()

    assert events == [
        ("initialize", "first"),
        ("initialize", "second"),
        ("execute", "first"),
        ("execute", "second"),
    ]

    events.clear()

    runner.run(second)
    runner.run(first)
    runner.execute()

    assert events == [("execute", "second"), ("execute", "first")]


def test_command_runner_delegates_initialize_exception_to_robot():
    robot, runner = make_runner()
    command = RaiseOnInitialize()

    runner.run(command)
    runner.execute()

    assert robot.on_exception_calls == 1


def test_command_runner_delegates_execute_exception_to_robot():
    robot, runner = make_runner()
    command = RaiseOnExecute()

    runner.run(command)
    runner.execute()

    assert robot.on_exception_calls == 1


def test_command_runner_delegates_end_exception_to_robot():
    robot, runner = make_runner()
    command = RaiseOnEnd()

    runner.run(command)
    runner.execute()

    assert robot.on_exception_calls == 1


def test_command_runner_works_as_magicbot_component():
    robot = make_component_robot()

    robot.first.should_run = True
    robot.first.execute()
    robot.cmd.execute()

    assert robot.first.command.initialize_calls == 1
    assert robot.first.command.execute_calls == 1


def test_command_runner_supports_basic_command_group():
    _, runner = make_runner()
    first = RecordingCommand(finished_after=1)
    second = RecordingCommand(finished_after=1)
    group = commands2.cmd.sequence(first, second)

    runner.run(group)
    runner.execute()
    runner.run(group)
    runner.execute()

    assert first.initialize_calls == 1
    assert first.execute_calls == 1
    assert first.end_calls == [False]
    assert second.initialize_calls == 1
    assert second.execute_calls == 1
    assert second.end_calls == [False]
