import pytest


@pytest.mark.parametrize("enabled", [False, True])
def test_early_autonomous_exit(control, robot, enabled):
    with control.run_robot():
        control.step_timing(seconds=0.5, autonomous=True, enabled=False)
        control.step_timing(seconds=0.3, autonomous=True, enabled=True)
        assert robot.drive.output == 0.5

        control.step_timing(seconds=0.1, autonomous=False, enabled=enabled)
        assert robot.drive.output == 0.0
        distance = robot.drive.distance
        control.step_timing(seconds=0.5, autonomous=False, enabled=True)
        assert robot.drive.distance == distance
        assert not robot.runner._active


def test_library_command_autonomous(control, robot):
    with control.run_robot():
        control.step_timing(seconds=0.5, autonomous=True, enabled=False)
        assert robot.auto_commands.runner is robot.runner
        assert robot.auto_commands.drive is robot.drive
        command = robot.auto_commands.command

        for _ in range(2):
            start_distance = robot.drive.distance
            control.step_timing(seconds=0.5, autonomous=True, enabled=True)
            assert robot.drive.output == 0.5
            assert robot.drive.distance > start_distance

            control.step_timing(seconds=1.0, autonomous=True, enabled=True)
            assert robot.drive.output == 0.0
            assert robot.drive.distance - start_distance == pytest.approx(0.5, abs=0.03)
            assert robot.auto_commands.command is command

            end_distance = robot.drive.distance
            control.step_timing(seconds=0.5, autonomous=True, enabled=True)
            assert robot.drive.distance == end_distance
            control.step_timing(seconds=0.5, autonomous=True, enabled=False)
