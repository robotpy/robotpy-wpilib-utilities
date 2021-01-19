from robotpy_ext.control.toggle import Toggle
from robotpy_ext.misc.precise_delay import NotifierDelay


class FakeJoystick:
    def __init__(self):
        self._pressed = [False] * 2

    def getRawButton(self, num):
        return self._pressed[num]

    def press(self, num):
        self._pressed[num] = True

    def release(self, num):
        self._pressed[num] = False


def test_toggle():
    joystick = FakeJoystick()
    toggleButton = Toggle(joystick, 0)
    toggleButton2 = Toggle(joystick, 1)
    assert toggleButton.off
    joystick.press(0)
    assert toggleButton.on
    assert toggleButton2.off
    joystick.release(0)
    assert toggleButton.on
    joystick.press(0)
    assert toggleButton.off
    joystick.release(0)
    assert toggleButton.off
    joystick.press(1)
    assert toggleButton.off
    assert toggleButton2.on


def test_toggle_debounce():
    # TODO: use simulated time
    delay = NotifierDelay(0.5)
    joystick = FakeJoystick()
    toggleButton = Toggle(joystick, 1, 0.1)
    assert toggleButton.off
    joystick.press(1)
    assert toggleButton.on
    joystick.release(1)
    joystick.press(1)
    joystick.release(1)
    assert toggleButton.on
    delay.wait()
    assert toggleButton.on
    joystick.press(1)
    assert toggleButton.off
