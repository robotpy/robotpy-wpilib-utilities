import logging
from pyfrc.test_support.controller import TestController as PyfrcTestController
from ntcore.util import ChooserControl


autonomous_seconds = 15


def test_all_autonomous(control: PyfrcTestController):
    """
    This test runs all possible autonomous modes that can be selected
    by the autonomous switcher.

    This should work for most robots. If it doesn't work for yours,
    and it's not a code issue with your robot, please file a bug on
    github.
    """

    logger = logging.getLogger("test-all-autonomous")

    with control.run_robot():
        # Run disabled for a short period, chooser needs to be
        # initialized in robotInit
        control.step_timing(seconds=0.5, autonomous=True, enabled=False)

        # retrieve autonomous modes from chooser here
        chooser = ChooserControl("Autonomous Mode")
        choices = chooser.getChoices()
        if len(choices) == 0:
            return

        for choice in choices:
            chooser.setSelected(choice)
            logger.info(f"{'='*10} Testing '{choice}' {'='*10}")

            # Run disabled for a short period
            control.step_timing(seconds=0.5, autonomous=True, enabled=False)

            # Run enabled for 15 seconds
            control.step_timing(
                seconds=autonomous_seconds, autonomous=True, enabled=True
            )

            # Disabled for another short period
            control.step_timing(seconds=0.5, autonomous=True, enabled=False)
