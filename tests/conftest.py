# TODO: remove this once WPILib is public, and use the real thing

import sys
from unittest.mock import MagicMock

import pytest


def pytest_runtest_setup():
    pass


def pytest_runtest_teardown():
    pass


@pytest.fixture(scope="function")
def wpimock(monkeypatch):
    mock = MagicMock(name="wpimock")
    monkeypatch.setitem(sys.modules, "wpilib", mock)
    return mock


@pytest.fixture(scope="function")
def wpitime():
    import hal.simulation

    class FakeTime:
        def step(self, seconds):
            delta = int(seconds * 1e9)  # nanoseconds
            hal.simulation.step_timing_async(delta)

    hal.simulation.pause_timing()
    hal.simulation.restart_timing()

    yield FakeTime()

    hal.simulation.resume_timing()


@pytest.fixture(scope="function")
def hal(wpitime):
    import hal.simulation

    yield

    # Reset the HAL handles
    hal.simulation.reset_global_handles()

    # Reset the HAL data
    hal.simulation.reset_all_sim_data()
