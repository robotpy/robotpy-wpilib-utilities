import time


def wait_until(control, predicate):
    # Mode transitions run outside the notifier loop. Yield to the robot thread
    # rather than assuming a fixed amount of simulated time starts autonomous.
    for _ in range(30):
        control.step_timing(seconds=0.1, autonomous=True, enabled=True)
        time.sleep(0.001)
        if predicate():
            return
    assert predicate(), "Autonomous did not reach the expected state/output"


def test_two_steps(control, robot):
    """Verify injection, timed transitions, and per-cycle reset behavior."""
    with control.run_robot():
        control.step_timing(seconds=0.5, autonomous=True, enabled=False)
        assert robot.component2.component1 is robot.component1
        assert robot.component2.some_motor is robot.some_motor
        assert robot.component2.SOME_CONSTANT == robot.SOME_CONSTANT

        wait_until(
            control,
            lambda: robot._automodes.active_mode is not None
            and robot._automodes.active_mode.current_state == "dont_do_something",
        )
        control.step_timing(seconds=1, autonomous=True, enabled=True)
        assert robot.some_motor.get_throttle() == 0

        wait_until(control, lambda: robot.some_motor.get_throttle() == 1)
        control.step_timing(seconds=3, autonomous=True, enabled=True)
        assert robot.some_motor.get_throttle() == 1
        wait_until(control, lambda: robot.some_motor.get_throttle() == 0)
        control.step_timing(seconds=1, autonomous=True, enabled=True)
        assert robot.some_motor.get_throttle() == 0
