import logging


class MagicComponent:
    """
    To automagically retrieve variables defined in your base robot
    object, you can add the following::

        class MyComponent:

            # other variables 'imported' automatically from MagicRobot
            elevator_motor: Talon
            other_component: MyOtherComponent

            ...

            def execute(self):

                # This will be automatically set to the Talon
                # instance created in robot.py
                self.elevator_motor.set(self.value)


    What this says is "find the variable in the robot class called
    'elevator_motor', which is a Talon". If the name and type match,
    then the variable will automatically be injected into your
    component when it is created.

    .. note:: You don't need to inherit from ``MagicComponent``, it is only
              provided for documentation's sake
    """

    logger: logging.Logger

    def setup(self):
        """
        This function is called after ``createObjects`` has been called in
        the main robot class, and after all components have been created

        The setup function is optional and components do not have to define
        one. ``setup()`` functions are called in order of component definition
        in the main robot class.

        .. note:: For technical reasons, variables imported from
                  MagicRobot are not initialized when your component's
                  constructor is called. However, they will be initialized
                  by the time this function is called.
        """

    def on_enable(self):
        """
        Called when the robot enters autonomous or teleoperated mode. This
        function should initialize your component to a "safe" state so
        that unexpected things don't happen when enabling the robot.

        .. note:: You'll note that there isn't a separate initialization
                  function for autonomous and teleoperated modes. This is
                  intentional, as they should be the same.
        """

    def on_disable(self):
        """
        Called when the robot leaves autonomous or teleoperated
        """

    def execute(self):
        """
        This function is called at the end of the control loop
        """
