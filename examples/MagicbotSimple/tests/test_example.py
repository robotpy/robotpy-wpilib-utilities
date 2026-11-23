def test_two_steps(control, robot):
    """Verify injection, timed transitions, and per-cycle reset behavior."""
    with control.run_robot():
        control.step_timing(seconds=0.5, autonomous=True, enabled=False)
        assert robot.component2.component1 is robot.component1
        assert robot.component2.some_motor is robot.some_motor
        assert robot.component2.SOME_CONSTANT == robot.SOME_CONSTANT

        control.step_timing(seconds=1, autonomous=True, enabled=True)
        assert robot.some_motor.get_throttle() == 0
        control.step_timing(seconds=2, autonomous=True, enabled=True)
        assert robot.some_motor.get_throttle() == 1
        control.step_timing(seconds=5, autonomous=True, enabled=True)
        assert robot.some_motor.get_throttle() == 0
