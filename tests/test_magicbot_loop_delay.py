import threading
from pathlib import Path

import pytest
import wpilib.simulation as sim

from magicbot import MagicRobot
from wpilib.testing.pytest_plugin import RobotTestingPlugin


class LoopDelayRobot(MagicRobot):
    def create_objects(self):
        pass


# Use WPILib's real simulation setup, controller, and teardown locally rather
# than applying robot fixtures to the other framework tests.
_plugin = RobotTestingPlugin(LoopDelayRobot, Path(__file__), isolated=False)
robot = _plugin.robot
control = _plugin.control


def test_shared_delay_across_enabled_modes(control, robot, monkeypatch):
    entered = {mode: threading.Event() for mode in ("disabled", "autonomous", "teleop")}
    delays = {}

    def instrument(mode):
        original = getattr(robot, mode + "_init")

        def init():
            delays[mode] = robot._loop_delay
            original()
            entered[mode].set()

        monkeypatch.setattr(robot, mode + "_init", init)

    for mode in entered:
        instrument(mode)

    with control.run_robot():
        control.step_timing(seconds=0.1, autonomous=True, enabled=False)
        assert entered["disabled"].wait(2)
        control.step_timing(seconds=0.1, autonomous=True, enabled=True)
        assert entered["autonomous"].wait(2)
        control.step_timing(seconds=0.1, autonomous=False, enabled=True)
        assert entered["teleop"].wait(2)
        assert delays["disabled"] is not None
        assert delays["disabled"] is delays["autonomous"] is delays["teleop"]


@pytest.mark.parametrize("mode", ["disabled", "autonomous", "teleop"])
def test_run_robot_shutdown(control, robot, mode):
    try:
        with control.run_robot():
            control.step_timing(
                seconds=0.1,
                autonomous=mode == "autonomous",
                enabled=mode != "disabled",
            )
            assert robot._loop_delay is not None
        assert not control.robot_is_alive
        assert robot._loop_delay is None
    finally:
        # Also unblock the worker if an assertion inside the context fails:
        # the controller's normal async step is skipped on exceptional exit.
        robot.end_competition()
        sim.step_timing_async(1.0)
        thread = control._thread
        if thread is not None:
            thread.join(2)
            assert not thread.is_alive()
