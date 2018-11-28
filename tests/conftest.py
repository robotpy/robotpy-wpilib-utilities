# TODO: remove this once WPILib is public, and use the real thing

import sys

import pytest
from unittest.mock import MagicMock, call


class FakeSensorBase:
    pass


def pytest_runtest_setup():
    import networktables

    networktables.NetworkTables.startTestMode()


def pytest_runtest_teardown():
    import networktables

    networktables.NetworkTables.shutdown()

    from wpilib import SmartDashboard

    SmartDashboard._reset()


@pytest.fixture(scope="function")
def wpimock(monkeypatch):
    mock = MagicMock(name="wpimock")
    mock.SensorBase = FakeSensorBase
    monkeypatch.setitem(sys.modules, "wpilib", mock)
    return mock


@pytest.fixture(scope="function")
def wpitime(monkeypatch):
    class FakeTime:
        def __init__(self):
            self.now = 0  # in seconds

        def getFPGATime(self):
            return self.now * 1000000

    ft = FakeTime()

    import hal

    monkeypatch.setattr(hal, "getFPGATime", ft.getFPGATime)

    return ft
