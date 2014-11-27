
# TODO: remove this once WPILib is public, and use the real thing

import sys

import pytest
from unittest.mock import MagicMock, call

class FakeSensorBase:
    pass

@pytest.fixture(scope="function")
def wpimock(monkeypatch):
    mock = MagicMock(name='wpimock')
    mock.SensorBase = FakeSensorBase
    monkeypatch.setitem(sys.modules, 'wpilib', mock)
    return mock