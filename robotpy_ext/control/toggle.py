from functools import partial

import wpilib


class Toggle:
    """Utility class for joystick button toggle

    Usage::

        foo = Toggle(joystick, 3)

        if foo:
            toggleFunction()

        if foo.on:
            onToggle()

        if foo.off:
            offToggle()
    """

    class _SteadyDebounce:
        """
        Similar to ButtonDebouncer, but the output stays steady for
        the given periodic_filter. E.g, if you set the period to 2
        and press the button, the value will return true for 2 seconds.

        Steady debounce will return true for the given period, allowing it to be
        used with Toggle
        """

        def __init__(self, joystick: wpilib.Joystick, button: int, period: float):
            """
            :param joystick:  Joystick object
            :type  joystick:  :class:`wpilib.Joystick`
            :param button: Number of button to retrieve
            :type  button: int
            :param period:    Period of time (in seconds) to wait before allowing new button
                              presses. Defaults to 0.5 seconds.
            :type  period:    float
            """
            self.joystick = joystick
            self.button = button

            self.debounce_period = float(period)
            self.latest = (
                -self.debounce_period
            )  # Negative latest prevents get from returning true until joystick is presed for the first time
            self.enabled = False

        def get(self):
            """
            :returns: The value of the joystick button. Once the button is pressed,
            the return value will be `True` until the time expires
            """

            now = wpilib.Timer.getFPGATimestamp()
            if now - self.latest < self.debounce_period:
                return True

            if self.joystick.getRawButton(self.button):
                self.latest = now
                return True
            else:
                return False

    def __init__(
        self, joystick: wpilib.Joystick, button: int, debounce_period: float = None
    ):
        """
        :param joystick: :class:`wpilib.Joystick` that contains the button to toggle
        :param button: Number of button that will act as toggle. Same value used in `getRawButton()`
        :param debounce_period: Period in seconds to wait before registering a new button press.
        """

        if debounce_period is not None:
            self.joystickget = Toggle._SteadyDebounce(
                joystick, button, debounce_period
            ).get
        else:
            self.joystick = joystick
            self.joystickget = partial(self.joystick.getRawButton, button)

        self.released = False
        self.toggle = False
        self.state = False

    def get(self):
        """
        :return: State of toggle
        :rtype: bool
        """
        current_state = self.joystickget()

        if current_state and not self.released:
            self.released = True
            self.toggle = not self.toggle
            self.state = not self.state  # Toggles between 1 and 0.

        elif not current_state and self.released:
            self.released = False

        return self.toggle

    @property
    def on(self):
        """
        Equates to true if toggle is in the 'on' state
        """
        self.get()
        return self.state

    @property
    def off(self):
        """
        Equates to true if toggle is in the 'off' state
        """
        self.get()
        return not self.state

    __bool__ = get
