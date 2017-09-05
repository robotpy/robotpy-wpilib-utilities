from _functools import partial
from wpilib.timer import Timer


class Toggle:
    """Utility class for button toggle

        Usage:

        foo = Toggle(joystick, 3)

        if foo:
            toggleFunction()

        if foo.on:
            onToggle()

        if foo.off:
            offToggle()
    """
    class _SteadyDebounce:
        '''
            Similar to ButtonDebouncer, but the output stays steady for
            the given periodic_filter. E.g, if you set the period to 2
            and press the button, the value will return true for 2 seconds.

            Steady debounce will return true for the given period, allowing it to be
            used with Toggle
        '''

        def __init__(self, joystick, button, period=0.5):
            '''
            :param joystick:  Joystick object
            :type  joystick:  :class:`wpilib.Joystick`
            :param button: Number of button to retrieve
            :type  button: int
            :param period:    Period of time (in seconds) to wait before allowing new button
                              presses. Defaults to 0.5 seconds.
            :type  period:    float
            '''
            self.joystick = joystick
            self.button = button

            self.debounce_period = float(period)
            self.latest = - self.debounce_period # Negative latest prevents get from returning true until joystick is presed for the first time
            self.timer = Timer
            self.enabled = False

        def set_debounce_period(self, period):
            '''Set number of seconds to hold return value'''
            self.debounce_period = float(period)

        def get(self):
            '''Returns the value of the joystick button. Once the button is pressed,
            the return value will be True until the time expires
            '''

            now = self.timer.getFPGATimestamp()
            if now - self.latest < self.debounce_period:
                return True

            if self.joystick.getRawButton(self.button):
                self.latest = now
                return True
            else:
                return False

    def __init__(self, joystick, button, debouncePeriod=None):
        """
        :param joystick: wpilib.Joystick that contains the button to toggle
        :param button: Value of button that will act as toggle. Same value used in getRawButton()
        """

        if debouncePeriod is not None:
            self.joystick = Toggle._SteadyDebounce(joystick, button, debouncePeriod)
        else:
            self.joystick = joystick
            self.joystick.get = partial(self.joystick.getRawButton, button)

        self.released = False
        self.toggle = False
        self.state = False

    def get(self):
        """
         :return: State of toggle
         :rtype: bool
         """
        current_state = self.joystick.get()

        if current_state and not self.released:
            self.released = True
            self.toggle = not self.toggle
            self.state = not self.state # Toggles between 1 and 0.

        elif not current_state and self.released:
            self.released = False

        return self.toggle

    @property
    def on(self):
        self.get()
        return self.state

    @property
    def off(self):
        self.get()
        return not self.state

    __bool__ = get
