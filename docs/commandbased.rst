Command Based Robot
===================

If you're coming from C++ or Java, you are probably familiar with the `Command based robot paradigm <https://wpilib.screenstepslive.com/s/4485/m/13810/l/241892-what-is-command-based-programming>`_. All of the pieces you're used to are still here, but this guide might help save you a bit of time as you make the transition.

If you're starting Command based programming in Python and have no experience with it in other languages, make sure you familiarize yourself with it before proceeding. This guide only covers differences between Python and the other languages's versions of that paradigm.

For the impatient, a `fully-working example program <https://github.com/robotpy/robotpy-wpilib-utilities/tree/master/samples/command_based>`_ is available. You can start with that and modify it to meet your needs.

The Basics
----------
The structure of a Command based program is simple and predictable. You inherit from the ``IterativeRobot`` class, configure the robot in ``robotInit()``, and then run the ``Scheduler`` inside the ``*Periodic()`` methods.

Writing it can be done rather quickly, but the robotpy-wpilib-utilities package contains a pre-built skeleton class you can inherit, meaning that your program only needs to implement functions unique to your robot. Here is an example::

    import wpilib
    from commandbased import CommandBasedRobot

    from commands import AutonomousCommandGroup

    class MyRobot(CommandBasedRobot):

        def robotInit(self):
            '''Initialize things like subsystems'''

            self.autonomous = AutonomousCommandGroup()


        def autonomousInit(self):
            self.autonomous.start()


Setting up the scheduler and running it are handled by the CommandBasedRobot class. You only need to write the code for ``*Init()`` methods you want to use. Since you are overriding that class, you can easily change any functionality that doesn't work for your robot, though `the default implementation <https://github.com/robotpy/robotpy-wpilib-utilities/blob/master/commandbased/commandbasedrobot.py>`_ should work for most cases.

Error Handling
--------------
Crashes happen. Even the most careful programmer can write a command that breaks under unexpected conditions. Normally this will cause your program to reboot, costing precious seconds during a competition. With this in mind, the ``Scheduler`` is run inside an exception handler. If a crash happens inside a Command while your robot is connection to the Field Management System (i.e. - during a competition) the exception will be caught, running commands will be canceled, the error will be printed on the driver's station, and the Scheduler loop will continue running normally.

If you need more advanced error handling functionality, you can override the ```handleCrash()``` method in your robot.py.

Pythonic Command Based Programming
----------------------------------
All the classes you know from C++ and Java still exists in Python, allowing you to directly port your code with minimal changes. However, you can use some of the advantages of Python to make a few things a bit easier.

Subsystems
~~~~~~~~~~
In C++ and Java, the recommended way of making subsystems available to Commands is to instantiate them in the ``init()`` method of a class that subclasses ``Command``, and then use that as the base class for all of your classes. Even in those languages that can be a bit unwieldy, especially if you want your commands to inherit from multiple base classes.

A more appropriate method in Python is to instantiate your subsystems inside a module, then import that module anywhere you need subsystems. Here is a simple example of that module, which we will call ``subsystems``::

    from subsystemtype import SubsystemType

    subsystem1 = None

    def init():
        global subsystem1

        subsystem1 = SubsystemType()

You can import this module in your ``robot.py`` and then call ``subsystems.init()`` inside ``robotInit()`` before any commands are instantiated. Then you can access your subsystem from any Command like this::

    import subsystems
    from wpilib.command import InstantCommand

    class ExampleCommand(InstantCommand):

        def __init__(self):
            self.requires(subsystems.subsystem1)

        def initialize(self):
            subsystems.subsystem1.do_something()

By using this method you can override any Command provided by WPILib or robotpy-wpilib-utilities, with pythonic namespacing. For even better structure, make ``subsystems`` a package that holds the code for all of your subsystems, as demonstrated in the `example program <https://github.com/robotpy/robotpy-wpilib-utilities/tree/master/samples/command_based/subsystems>`_.

RobotMap
~~~~~~~~
Having a single place to store your robot's configuration can be very helpful, and this is why most Command based robots integrate a ``RobotMap.*`` file to store port numbers. In Python you can create a ``robotmap`` module that will act similarly. There are many different possible ways to manage your ports:

1.) Raw variables::

    drive_front_left = 1
    drive_front_right = 2
    drive_rear_left = 3
    drive_rear_right = 4

2.) Dictionary::

    drive = {
        'front_left': 1,
        'front_right': 2,
        'rear_left': 3,
        'rear_right': 4
    }

3.) Object Properties::

    class PortList():
        pass

    drive = PortList()

    drive.front_left = 1
    drive.front_right = 2
    drive.rear_left = 3
    drive.rear_right = 4

Whichever method you choose, you can utilize it simply by importing::

    import robotmap
    from wpilib.command import Subsystem

    class DriveSubsystem(Subsystem):
        def __init__():
            front_left_motor = robotmap.drive_front_left

Final Thoughts
--------------
Welcome to FRC programming with Python. This documentation is still developing, so if you find a great trick to make programming your robot in the Command based paradigm more "pythonic", please update it with your ideas.
