
import inspect
import logging

import wpilib

from robotpy_ext.misc import PreciseDelay
from robotpy_ext.autonomous import AutonomousModeSelector

from robotpy_ext.misc.orderedclass import OrderedClass

from networktables import NetworkTable

__all__ = ['MagicRobot']

class MagicRobot(wpilib.SampleRobot,
                 metaclass=OrderedClass):
    """
        .. warning:: This implementation is still being developed, and may
                     be changed during the course of the 2016 season.

        Robots that use the MagicBot framework should use this as their
        base robot class. If you use this as your base, you must
        implement the following methods:

        - :meth:`createObjects`
        - :meth:`teleopPeriodic`

        MagicRobot uses the :class:`.AutonomousModeSelector` to allow you
        to define multiple autonomous modes and to select one of them via
        the SmartDashboard/SFX.
        
        MagicRobot will set the following NetworkTables variables
        automatically:
        
        - ``/robot/mode``: one of 'disabled', 'auto', 'teleop', or 'test'
        - ``/robot/is_simulation``: True/False
        
    """

    #: Amount of time each loop takes (default is 20ms)
    control_loop_wait_time = 0.020

    #: Error report interval: when an FMS is attached, how often should
    #: uncaught exceptions be reported?
    error_report_interval = 0.5

    def robotInit(self):
        """
            .. warning:: Internal API, don't override; use :meth:`createObjects` instead
        """

        self._exclude_from_injection = [
            'logger', 'members'
        ]

        self.__last_error_report = -10

        self._components = []

        # Create the user's objects and stuff here
        self.createObjects()

        # Load autonomous modes
        self._automodes = AutonomousModeSelector('autonomous')

        # Next, create the robot components and wire them together
        self._create_components()
        
        self.__nt = NetworkTable.getTable('/robot')
        self.__nt.putBoolean('is_simulation', self.isSimulation())

    def createObjects(self):
        """
            You should override this and initialize all of your wpilib
            objects here (and not in your components, for example). This
            serves two purposes:

            - It puts all of your motor/sensor initialization in the same
              place, so that if you need to change a port/pin number it
              makes it really easy to find it. Additionally, if you want
              to create a simplified robot program to test a specific
              thing, it makes it really easy to copy/paste it elsewhere

            - It allows you to use the magic injection mechanism to share
              variables between components

            .. note:: Do not access your magic components in this function,
                      as their instances have not been created yet. Do not
                      create them either.
        """
        raise NotImplementedError

    def teleopInit(self):
        """
            Initialization code for teleop control code may go here.

            Users may override this method for initialization code which will be
            called each time the robot enters teleop mode.

            .. note:: The ``on_enable`` functions of all components are called
                      before this function is called.
        """
        pass

    def teleopPeriodic(self):
        """
            Periodic code for teleop mode should go here.

            Users should override this method for code which will be called
            periodically at a regular rate while the robot is in teleop mode.

            This code executes before the ``execute`` functions of all
            components are called.
        """
        func = self.teleopPeriodic.__func__
        if not hasattr(func, "firstRun"):
            self.logger.warn("Default MagicRobot.teleopPeriodic() method... Overload me!")
            func.firstRun = False

    def disabledInit(self):
        """
            Initialization code for disabled mode may go here.

            Users may override this method for initialization code which will be
            called each time the robot enters disabled mode.

            .. note:: The ``on_disable`` functions of all components are called
                      before this function is called.
        """
        pass

    def disabledPeriodic(self):
        """
            Periodic code for disabled mode should go here.

            Users should override this method for code which will be called
            periodically at a regular rate while the robot is in disabled mode.

            This code executes before the ``execute`` functions of all
            components are called.
        """
        func = self.disabledPeriodic.__func__
        if not hasattr(func, "firstRun"):
            self.logger.warn("Default MagicRobot.disabledPeriodic() method... Overload me!")
            func.firstRun = False

    def onException(self, forceReport=False):
        '''
            This function must *only* be called when an unexpected exception
            has occurred that would otherwise crash the robot code. Use this
            inside your :meth:`operatorActions` function.

            If the FMS is attached (eg, during a real competition match),
            this function will return without raising an error. However,
            it will try to report one-off errors to the Driver Station so
            that it will be recorded in the Driver Station Log Viewer.
            Repeated errors may not get logged.

            Example usage::

                def teleopPeriodic(self):
                    try:
                        if self.joystick.getTrigger():
                            self.shooter.shoot()
                    except:
                        self.onException()

                    try:
                        if self.joystick.getRawButton(2):
                            self.ball_intake.run()
                    except:
                        self.onException()

                    # and so on...

            :param forceReport: Always report the exception to the DS. Don't
                                set this to True
        '''
        # If the FMS is not attached, crash the robot program
        if not self.ds.isFMSAttached():
            raise

        # Otherwise, if the FMS is attached then try to report the error via
        # the driver station console. Maybe.
        now = wpilib.Timer.getFPGATimestamp()

        try:
            if forceReport or (now - self.__last_error_report) > self.error_report_interval:
                wpilib.DriverStation.reportError("Unexpected exception", True)
        except:
            pass    # ok, can't do anything here

        self.__last_error_report = now

    #
    # Internal API
    #

    def autonomous(self):
        """
            MagicRobot will do The Right Thing and automatically load all
            autonomous mode routines defined in the autonomous folder.

            .. warning:: Internal API, don't override
        """
        
        self.__nt.putString('mode', 'auto')

        self._on_mode_enable_components()

        self._automodes.run(self.control_loop_wait_time,
                            self._execute_components,
                            self.onException)

        self._on_mode_disable_components()


    def disabled(self):
        """
            This function is called in disabled mode. You should not
            override this function; rather, you should override the
            :meth:`disabledPeriodic` function instead.

            .. warning:: Internal API, don't override
        """
        
        self.__nt.putString('mode', 'disabled')

        delay = PreciseDelay(self.control_loop_wait_time)

        self._on_mode_disable_components()
        try:
            self.disabledInit()
        except:
            self.onException(forceReport=True)

        while self.isDisabled():
            try:
                self.disabledPeriodic()
            except:
                self.onException()

            delay.wait()

    def operatorControl(self):
        """
            This function is called in teleoperated mode. You should not
            override this function; rather, you should override the
            :meth:`teleopPeriodics` function instead.

            .. warning:: Internal API, don't override
        """
        
        self.__nt.putString('mode', 'teleop')

        delay = PreciseDelay(self.control_loop_wait_time)

        # initialize things
        self._on_mode_enable_components()

        try:
            self.teleopInit()
        except:
            self.onException(forceReport=True)

        while self.isOperatorControl() and self.isEnabled():
            try:
                self.teleopPeriodic()
            except:
                self.onException()

            self._execute_components()
            delay.wait()

        self._on_mode_disable_components()

    def test(self):
        '''Called when the robot is in test mode'''
        
        self.__nt.putString('mode', 'test')
        
        while self.isTest() and self.isEnabled():
            wpilib.LiveWindow.run()
            wpilib.Timer.delay(.01)

    def _on_mode_enable_components(self):
        # initialize things
        for component in self._components:
            if hasattr(component, 'on_enable'):
                try:
                    component.on_enable()
                except:
                    self.onException(forceReport=True)

    def _on_mode_disable_components(self):
        # deinitialize things
        for component in self._components:
            if hasattr(component, 'on_disable'):
                try:
                    component.on_disable()
                except:
                    self.onException(forceReport=True)

    def _create_components(self):

        #
        # TODO: Will need to inject into any autonomous mode component
        #       too, as they're a bit different
        #

        # TODO: Will need to order state machine components before
        #       other components just in case

        components = []
        
        self.logger.info("Creating magic components")

        # Identify all of the types, and create them
        for m in self.members:
            if m.startswith('_'):
                continue

            ctyp = getattr(self, m)
            if not isinstance(ctyp, type):
                continue

            # Create instance, set it on self
            component = ctyp()
            setattr(self, m, component)

            # Ensure that mandatory methods are there
            if not hasattr(component, 'execute') or \
               not callable(component.execute):
                raise ValueError("Component %s (%s) must have a method named 'execute'" % (m, component))

            # Automatically inject a logger object
            component.logger = logging.getLogger(m)

            # Store for later
            components.append((m, component))
            
            self.logger.info("-> %s (class: %s)", m, ctyp.__name__)

        # Collect attributes of this robot that are injectable
        self._injectables = {}

        for n in dir(self):
            if n.startswith('_') or n in self._exclude_from_injection:
                continue

            o = getattr(self, n)

            # Don't inject methods
            # TODO: This could actually be a cool capability..
            if inspect.ismethod(o):
                continue

            self._injectables[n] = o

        # For each new component, perform magic injection
        for cname, component in components:
            self._components.append(component)
            self._inject_vars(cname, component)

        # Do it for autonomous modes too
        for mode in self._automodes.modes.values():
            self._inject_vars(None, mode)


    def _inject_vars(self, cname, component):
        
        self.logger.debug("Injecting magic variables into %s", cname)
        
        for n in dir(component):
            if n.startswith('_'):
                continue

            inject_type = getattr(component, n)
            if not isinstance(inject_type, type):
                continue

            injectable = self._injectables.get(n)
            if injectable is None:
                if cname is not None:
                    injectable = self._injectables.get('%s_%s' % (cname, n))

            if injectable is None:
                raise ValueError("Component %s has variable %s (type %s), which is not present in %s" %
                                 (cname, n, inject_type, self))

            if not isinstance(injectable, inject_type):
                raise ValueError("Component %s variable %s in %s are not the same types! (Got %s, expected %s)" %
                                 (cname, n, self, type(injectable), inject_type))

            setattr(component, n, injectable)
            self.logger.debug("-> %s as %s.%s", injectable, cname, n)

    def _execute_components(self):
        for component in self._components:
            try:
                component.execute()
            except:
                self.onException()
