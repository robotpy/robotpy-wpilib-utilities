
import sys
from unittest.mock import MagicMock, call

# TODO: better tests

def test_precise_delay(monkeypatch):

    wpimock = MagicMock()
    monkeypatch.setitem(sys.modules, 'wpilib', wpimock)

    from robotpy_ext.misc import PreciseDelay    

    delay = PreciseDelay(1)
    
    # Make sure the wait executes twice
    delay.timer.hasPeriodPassed.side_effect = [False, True]
    delay.wait()

    delay.timer.hasPeriodPassed.assert_has_calls([call(1), call(1)])



