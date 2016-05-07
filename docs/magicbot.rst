magicbot Package
================

.. warning:: The MagicBot framework is still under heavy development, and 
             will change extensively during the 2016 season. However, most
             changes are expected to be additional features, not breakages

MagicBot is an opinionated framework for creating Python robot programs for
the FIRST Robotics Competition. It is envisioned to be an easier to use
pythonic alternative to the Command framework -- but it's not quite there yet.

While MagicBot will tend to be more useful for complex multi-module programs,
it does remove some of the boilerplate associated with simple programs as
well.

Philosophy
----------

You should use the :class:`.MagicRobot` class as your base robot class. You'll 
note that it's similar to :class:`.IterativeRobot`::

    import magicbot
    import wpilib

    class MyRobot(magicbot.MagicRobot):
        
        def createObjects(self):
            '''Create motors and stuff here'''
            pass
            
        def teleopInit(self):
            '''Called when teleop starts; optional'''
            
        def teleopPeriodic(self):
            '''Called on each iteration of the control loop'''
            
    if __name__ == '__main__':
        wpilib.run(MyRobot)


A robot control program can be divided into several logical parts (think
drivetrain, forklift, elevator, etc). We refer to these parts as 
"Components". 

Components
^^^^^^^^^^

When you design your robot code, you should define each of the components
of your robot and order them in a hierarchy, with "low level" components
at the bottom and "high level" components at the top.

- "Low level" components are those that directly interact with physical
  hardware: drivetrain, elevator, grabber
- "High level" components are those that only interact with other
  components: these are generally automatic behaviors or encapsulation
  of multiple low level components into an easier to use component
  
Generally speaking, components should never interact with operator controls
such as joysticks. This allows the components to be used in autonomous mode
and in teleoperated mode.

Components should have three types of methods (excluding internal methods):

- Control methods
- Informational methods
- An ``execute`` method

**Control methods**

Think of these as 'verb' functions. In other words, calling one of these means
that you want that particular thing to happen.

Control methods store information necessary to perform a desired action, but
**do not actually execute the action**. They are generally called either from
``teleopPeriodic``, another component's control method, or from an autonomous
mode.

Example method names: raise_arm, lower_arm, shoot

**Informational methods**

These are basic methods that tell something about a component. They are typically
called from control methods, but may be called from execute as well.

Example method names: is_arm_lowered, ready_to_shoot

**execute method**

The ``execute`` method reads the data stored by the control methods, and then
sends data to output devices such as motors to execute the action. You should
not call the execute function as ``execute`` is automatically called by
MagicRobot if you define it as a magic component.

Component creation
^^^^^^^^^^^^^^^^^^

Components are instantiated by the MagicRobot class. You can tell the
:class:`.MagicRobot` class to create magic components by defining the
variable names and types in your MyRobot object.

.. code-block:: python

    from components import Elevator, Forklift

    class MyRobot(MagicRobot):
    
        elevator = Elevator
        forklift = Forklift
        
        def teleopPeriodic(self):
            
            # self.elevator is now an instance of Elevator


Variable injection
^^^^^^^^^^^^^^^^^^

To reduce boilerplate associated with passing components around, and to
enhance autocomplete for PyDev, MagicRobot can inject variables defined
in your robot class into other components, and autonomous modes. Check
out this example:

.. code-block:: python

    class MyRobot(MagicRobot):
    
        def createObjects(self):
            self.elevator_motor = wpilib.Talon(2)
    
    
    class Elevator:
    
        elevator_motor = wpilib.Talon
        
        def execute(self):
            # self.elevator_motor is a reference to the Talon instance
            # created in MyRobot.createObjects

Low level components
^^^^^^^^^^^^^^^^^^^^

Low level components are those that directly interact with hardware.

Here's an example low level component that 

    class Shooter:

        shooter_motor = wpilib.Talon


        def is_ready(self):
            pas

        def execute(self):
            pass


High level components
^^^^^^^^^^^^^^^^^^^^^

High level components are those that control other components to automate
one or more of them for automated behaviors. Consider the example of the
Shooter component above -- while it is usable, it's a bit klunky for an
operator to control, or to use from an autonomous mode.


Operator Control code
^^^^^^^^^^^^^^^^^^^^^

Code that controls components should go in the ``teleopPeriodic`` method.
This is really the only place that you should generally interact with a
Joystick or NetworkTables variable that directly triggers an action to
happen.

To ensure that a single portion of robot code cannot bring down your entire
robot program during a competition, MagicRobot provides an ``onException``
method that will either swallow the exception and report it to the Driver
Station, or if not connected to the FMS will crash the robot so that you
can inspect the error::

    try:
        if self.joystick.getTrigger():
            self.component.doSomething()
    except:
        self.onException()
        
        
.. note:: Most of the time when you write code, you never want to create
          generic exception handlers, but you should try to catch specific
          exceptions. However, this is a special case and we actually do want
          to catch all exceptions.

.. seealso:: `RobotPy Guidelines <http://robotpy.readthedocs.org/en/latest/guide/guidelines.html#don-t-die-during-the-competition>`_

Autonomous mode
---------------

MagicBot supports loading multiple autonomous modes from a python
package called 'autonomous'. To create this package, you must:

- Create a folder called 'autonomous' in the same directory as robot.py
- Add an empty file called '__init__.py' to that folder

Any ``.py`` files that you add to the autonomous package will
automatically be loaded at robot startup.

.. seealso:: :class:`.AutonomousModeSelector` on how to define an
             autonomous mode.

Dashboard & coprocessor communications
--------------------------------------

The simplest method to communicate with other programs external to your robot
code (examples include dashboards and image processing code) is using 
NetworkTables. NetworkTables is a distributed keystore, or put more simply,
it is similar to a python dictionary that is shared across multiple processes.


TODO: should include docs from `tunable` or make them different somehow.. or link
to them from here, this is a bit odd to dup
 
.. note:: For more information about NetworkTables, see TODO

Magicbot provides a simple way to interact with NetworkTables, using the
:func:`tunable` property. It provides a python property that has get/set
functions that read and write from NetworkTables. The NetworkTables key
is automatically determined by the name of your object instance and the
name of the attribute that the tunable is assigned to.

In the following example, this would create a NetworkTables variable called
`/components/mine/foo`, and assign it a default value of 1.0::

    class MyComponent:

        foo = tunable(default=1.0)

    ...

    class MyRobot:
        mine = MyComponent

To access the variable, in ``MyComponent`` you can read or write ``self.foo``
and it will read/write to NetworkTables.

For more information about creating custom dashboards, see the following:

* pynetworktables2js docs
* Smartdashboard docs?


     
magicbot module
----------------

.. automodule:: magicbot.magicrobot
    :members:
    :exclude-members: autonomous, disabled, members, operatorControl, robotInit, test
    :show-inheritance:

Component
^^^^^^^^^

.. automodule:: magicbot.magiccomponent
    :members:
    :undoc-members:
    :show-inheritance:

Tunable
^^^^^^^

.. automodule:: magicbot.magic_tunable
    :members:
    :undoc-members:
    :show-inheritance:

State machines
^^^^^^^^^^^^^^

.. automodule:: magicbot.state_machine
    :members:
    :exclude-members: members
    :undoc-members:
    :show-inheritance:
