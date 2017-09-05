from robotpy_ext.control.toggle import Toggle
from robotpy_ext.misc.precise_delay import PreciseDelay
class FakeJoystick:
    def __init__(self):
        self._pressed = False 
    
    def getRawButton(self, num):
        return self._pressed
    
    def press(self):
        self._pressed = True
    
    def release(self):
        self._pressed = False
    
def test_toggle():
    joystick = FakeJoystick()
    toggleButton = Toggle(joystick, 1)
    assert toggleButton.off
    joystick.press()
    assert toggleButton.on
    joystick.release()
    assert toggleButton.on
    joystick.press()
    assert toggleButton.off
    joystick.release()
    assert toggleButton.off


def test_toggle_debounce():
    delay = PreciseDelay(2.1)
    joystick = FakeJoystick()
    toggleButton = Toggle(joystick, 1, 2)
    assert toggleButton.off
    joystick.press()
    assert toggleButton.on
    joystick.release()
    joystick.press()
    joystick.release()
    assert toggleButton.on
    delay.wait()
    assert toggleButton.on
    joystick.press()
    assert toggleButton.off
