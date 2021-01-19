# TODO: remove this once WPILib is public, and use the real thing

import sys

import pytest
from unittest.mock import MagicMock


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
            delta = int(seconds * 1000000)
            hal.simulation.stepTimingAsync(delta)

    hal.simulation.pauseTiming()
    hal.simulation.restartTiming()

    yield FakeTime()

    hal.simulation.resumeTiming()
