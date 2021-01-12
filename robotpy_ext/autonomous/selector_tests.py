import pyfrc.config
import pytest
from networktables.util import ChooserControl

autonomous_seconds = 15
_gsms = pyfrc.config.config_obj["pyfrc"]["game_specific_messages"]


@pytest.mark.parametrize("gamedata", _gsms or [""])
def test_all_autonomous(control, fake_time, robot, gamedata):
    """
    This test runs all possible autonomous modes that can be selected
    by the autonomous switcher.

    This should work for most robots. If it doesn't work for yours,
    and it's not a code issue with your robot, please file a bug on
    github.
    """

    class AutonomousTester:
        def __init__(self):
            self.initialized = False
            self.init_time = None
            self.chooser = None

            self.state = "auto"
            self.currentChoice = None
            self.until = None

        def initialize_chooser(self, tm):

            if self.chooser is None:
                self.chooser = ChooserControl("Autonomous Mode")

            self.choices = self.chooser.getChoices()
            if len(self.choices) == 0:
                return False

            self.state = "disabled"
            self.currentChoice = -1
            self.until = tm
            self.init_time = tm
            self.initialized = True
            return True

        def on_step(self, tm):

            if not self.initialized:
                if not self.initialize_chooser(tm):
                    assert (
                        tm < 10
                    ), "Robot didn't create a chooser within 10 seconds, probably an error"
                    return True

            if self.state == "auto":
                if tm >= self.until:
                    self.until = tm + 1
                    self.state = "disabled"
                    control.set_operator_control(enabled=False)

            elif self.state == "disabled":
                if tm >= self.until:

                    control.set_autonomous()

                    self.state = "auto"
                    self.until = tm + autonomous_seconds
                    self.currentChoice += 1
                    if self.currentChoice >= len(self.choices):
                        return False

                    self.chooser.setSelected(self.choices[self.currentChoice])

            return True

    control.game_specific_message = gamedata
    controller = control.run_test(AutonomousTester)

    # Make sure they ran for the correct amount of time
    assert int(fake_time.get()) == int(
        len(controller.choices) * (autonomous_seconds + 1) + controller.init_time
    )
