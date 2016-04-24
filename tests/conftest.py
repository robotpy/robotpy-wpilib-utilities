
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

@pytest.fixture(scope='function')
def wpitime(monkeypatch):
    
    class FakeTime:
        def __init__(self):
            self.now = 0 # in seconds
            
        def getFPGATime(self):
            return self.now * 1000000
            
    ft = FakeTime()
    
    import hal
    monkeypatch.setattr(hal, 'getFPGATime', ft.getFPGATime)
    
    return ft
