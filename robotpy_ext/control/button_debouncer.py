import wpilib


class ButtonDebouncer:
    """Useful utility class for debouncing buttons"""

    def __init__(self, joystick, buttonnum, period=0.5):
        """
        :param joystick:  Joystick object
        :type  joystick:  :class:`wpilib.Joystick`
        :param buttonnum: Number of button to retrieve
        :type  buttonnum: int
        :param period:    Period of time (in seconds) to wait before allowing new button
                          presses. Defaults to 0.5 seconds.
        :type  period:    float
        """
        self.joystick = joystick
        self.buttonnum = buttonnum
        self.latest = 0
        self.debounce_period = float(period)
        self.timer = wpilib.Timer

    def set_debounce_period(self, period):
        """Set number of seconds to wait before returning True for the
        button again"""
        self.debounce_period = float(period)

    def get(self):
        """Returns the value of the joystick button. If the button is held down, then
        True will only be returned once every ``debounce_period`` seconds"""

        now = self.timer.getFPGATimestamp()
        if self.joystick.getRawButton(self.buttonnum):
            if (now - self.latest) > self.debounce_period:
                self.latest = now
                return True
        return False

    __bool__ = get
