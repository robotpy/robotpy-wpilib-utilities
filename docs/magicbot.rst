
.. _magicbot_api:

magicbot module
----------------

.. module:: magicbot

.. automodule:: magicbot.magicrobot
    :members:
    :exclude-members: autonomous, robot_init
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
stored ``commands2.Command`` instances until they finish or are cancelled.

Call ``self.cmd.run(command)`` once to start a stored command instance. It keeps
running without further requests until ``is_finished()`` returns true.
Call ``self.cmd.cancel(command)`` to interrupt an active command with
``end(True)`` or discard a pending command before it initializes.

When the robot is disabled, the runner interrupts all active commands and clears
pending requests. Commands never run while disabled. Autonomous modes should
also cancel their own commands when they exit, so commands do not continue into
teleop during a direct enabled mode transition.

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
