
.. _magicbot_api:

magicbot module
----------------

.. module:: magicbot

.. automodule:: magicbot.magicrobot
    :members:
    :exclude-members: autonomous, disabled, members, operatorControl, robotInit, test
    :show-inheritance:

Component
~~~~~~~~~

.. automodule:: magicbot.magiccomponent
    :members:
    :undoc-members:
    :show-inheritance:

Tunable
~~~~~~~

.. automodule:: magicbot.magic_tunable
    :members:
    :undoc-members:
    :exclude-members: feedback
    :show-inheritance:

.. autodecorator:: magicbot.magic_tunable.feedback

.. autoclass:: magicbot.magic_tunable._FeedbackDecorator
    :members:
    :undoc-members:
    :special-members: __call__

Resettable
~~~~~~~~~~

.. automodule:: magicbot.magic_reset
    :members:
    :undoc-members:
    :show-inheritance:

State machines
~~~~~~~~~~~~~~

.. automodule:: magicbot.state_machine
    :members:
    :exclude-members: members
    :undoc-members:
    :show-inheritance:

Commands
~~~~~~~~

.. automodule:: magicbot.commands
    :members:
    :undoc-members:
    :show-inheritance:

``magicbot.commands.CommandRunner`` is a MagicBot component that executes
stored ``commands2.Command`` instances using keep-alive semantics.

Call ``self.cmd.run(command)`` each loop that a stored command instance should
remain active. If a command is not re-requested on a later loop, it is ended as
interrupted when it is interruptible.

Important usage constraints:

- construct command instances once and store them on the robot/component
- do not create a new command inside ``execute()`` or a state method each loop
- components, state machines, and robot code may all call ``run(command)``
- multiple different commands may run concurrently
- this is not ``commands2.CommandScheduler`` and does not perform full
  scheduler-style requirement arbitration

Example::

    class Shooter:
        cmd: magicbot.commands.CommandRunner

        def setup(self):
            self.fire = FireCommand(...)

        def execute(self):
            if should_fire():
                self.cmd.run(self.fire)
