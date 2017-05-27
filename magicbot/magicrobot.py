
import contextlib
import inspect
import logging

import wpilib

from robotpy_ext.misc import PreciseDelay
from robotpy_ext.autonomous import AutonomousModeSelector

from robotpy_ext.misc.orderedclass import OrderedClass
from robotpy_ext.misc.annotations import get_class_annotations

from networktables import NetworkTable

from .magic_tunable import setup_tunables, _TunableProperty

__all__ = ['MagicRobot']

class MagicRobot(wpilib.SampleRobot,
                 metaclass=OrderedClass):
    """
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
        - ``/robot/is_ds_attached``: True/False
        
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
        self.__nt.putBoolean('is_ds_attached', self.ds.isDSAttached())

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
            self.logger.warning("Default MagicRobot.teleopPeriodic() method... Overload me!")
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
            self.logger.warning("Default MagicRobot.disabledPeriodic() method... Overload me!")
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

    @contextlib.contextmanager
    def consumeExceptions(self, forceReport=False):
        """
            This returns a context manager which will consume any uncaught
            exceptions that might otherwise crash the robot.

            Example usage::

                def teleopPeriodic(self):
                    with self.consumeExceptions():
                        if self.joystick.getTrigger():
                            self.shooter.shoot()

                    with self.consumeExceptions():
                        if self.joystick.getRawButton(2):
                            self.ball_intake.run()

                    # and so on...

            :param forceReport: Always report the exception to the DS. Don't
                                set this to True

            .. seealso:: :meth:`onException` for more details
        """
        try:
            yield
        except:
            self.onException(forceReport=forceReport)

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
        self.__nt.putBoolean('is_ds_attached', self.ds.isDSAttached())

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
        ds_attached = None

        delay = PreciseDelay(self.control_loop_wait_time)

        self._on_mode_disable_components()
        try:
            self.disabledInit()
        except:
            self.onException(forceReport=True)

        while self.isDisabled():
            
            if ds_attached != self.ds.isDSAttached():
                ds_attached = not ds_attached
                self.__nt.putBoolean('is_ds_attached', ds_attached)
            
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
        # don't need to update this during teleop -- presumably will switch
        # modes when ds is no longer attached
        self.__nt.putBoolean('is_ds_attached', self.ds.isDSAttached())

        delay = PreciseDelay(self.control_loop_wait_time)

        # initialize things
        self._on_mode_enable_components()

        try:
            self.teleopInit()
        except:
            self.onException(forceReport=True)

        while self.isOperatorControl() and self.isEnabled():
            
            #self._update_autosend()
            
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
        self.__nt.putBoolean('is_ds_attached', self.ds.isDSAttached())
        
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
        cls = self.__class__

        # - Iterate over class variables with type annotations
        for m, ctyp in get_class_annotations(cls).items():
            # Ignore private variables
            if m.startswith('_'):
                continue

            if hasattr(cls, m):
                attr = getattr(cls, m)
                # If the value given to the variable is an instance of a type and isn't a property
                # raise an error. No double declaring types, e.g foo: type = type
                if isinstance(attr, type) and not isinstance(attr, property):
                    raise ValueError("%s.%s has two type declarations" % (cls.__name__, m))
                continue

            # If the class variable has been assigned in __init__, skip it
            if hasattr(self, m):
                continue

            # If the type is not actually a type, give a meaningful error
            if not isinstance(ctyp, type):
                raise TypeError('%s has a non-type annotation on %s (%s); lone non-injection variable annotations are disallowed, did you want to assign a static variable?' %
                                (cls.__name__, m, ctyp))

            component = self._create_component(m, ctyp)

            # Store for later
            components.append((m, component))

        # - Iterate over set class variables
        for m in self.members:
            if m.startswith('_') or isinstance(getattr(cls, m, None), _TunableProperty):
                continue
            
            ctyp = getattr(self, m)
            if not isinstance(ctyp, type):
                continue

            component = self._create_component(m, ctyp)

            # Store for later
            components.append((m, component))

        # Collect attributes of this robot that are injectable
        self._injectables = {}

        for n in dir(self):
            if n.startswith('_') or n in self._exclude_from_injection or \
               isinstance(getattr(cls, n, None), _TunableProperty):
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
            setup_tunables(component, cname, 'components')
            self._setup_vars(cname, component)

        # Do it for autonomous modes too
        for mode in self._automodes.modes.values():
            mode.logger = logging.getLogger(mode.MODE_NAME)
            setup_tunables(mode, mode.MODE_NAME, 'autonomous')
            self._setup_vars(mode.MODE_NAME, mode)

        # And for self too
        setup_tunables(self, 'robot', None)
            
        # Call setup functions for components
        for cname, component in components:
            if hasattr(component, 'setup'):
                component.setup()

    def _create_component(self, name, ctyp):
        # Create instance, set it on self
        component = ctyp()
        setattr(self, name, component)

        # Ensure that mandatory methods are there
        if not callable(getattr(component, 'execute', None)):
            raise ValueError("Component %s (%s) must have a method named 'execute'" % (name, component))

        # Automatically inject a logger object
        component.logger = logging.getLogger(name)
        component._Magicbot__autosend = {}

        self.logger.info("-> %s (class: %s)", name, ctyp.__name__)

        return component
    
    def _setup_vars(self, cname, component):
        
        self.logger.debug("Injecting magic variables into %s", cname)
        
        component_type = type(component)
        
        # Iterate over variables with type annotations
        for n, inject_type in get_class_annotations(component_type).items():

            # If the variable is private ignore it
            if n.startswith('_'):
                continue

            if hasattr(component_type, n):
                attr = getattr(component_type, n)
                # If the value given to the variable is an instance of a type and isn't a property
                # raise an error. No double declaring types, e.g foo: type = type
                if isinstance(attr, type) and not isinstance(attr, property):
                    raise ValueError("%s.%s has two type declarations" % (component_type.__name__, n))
                continue

            # If the class variable has been assigned in __init__, skip it
            if hasattr(component, n):
                continue

            # If the type is not actually a type, give a meaningful error
            if not isinstance(inject_type, type):
                raise TypeError('Component %s has a non-type annotation on %s (%s); lone non-injection variable annotations are disallowed, did you want to assign a static variable?' %
                                (cname, n, inject_type))

            self._inject(n, inject_type, cname, component)

        # Iterate over static variables
        for n in dir(component):
            # If the variable is private or a proprty, don't inject
            if n.startswith('_') or isinstance(getattr(component_type, n, True), property):
                continue
            
            inject_type = getattr(component, n)
            
            # If the value assigned isn't a type, don't inject
            if not isinstance(inject_type, type):
                continue

            self._inject(n, inject_type, cname, component)

    def _inject(self, n, inject_type, cname, component):
        # Retrieve injectable object
        injectable = self._injectables.get(n)
        if injectable is None:
            if cname is not None:
                # Try for mangled names
                injectable = self._injectables.get('%s_%s' % (cname, n))

        # Raise error if injectable syntax used but no injectable was found.
        if injectable is None:
            raise ValueError("Component %s has variable %s (type %s), which is not present in %s" %
                             (cname, n, inject_type, self))
        
        # Raise error if injectable declared with type different than the initial type
        if not isinstance(injectable, inject_type):
            raise ValueError("Component %s variable %s in %s are not the same types! (Got %s, expected %s)" %
                             (cname, n, self, type(injectable), inject_type))
        # Perform injection
        setattr(component, n, injectable)
        self.logger.debug("-> %s as %s.%s", injectable, cname, n)

        # XXX
        #if is_autosend:
            # where to store the nt key?
        #    component._Magicbot__autosend[prop.f] = None
    
    #def _update_autosend(self):
    #    # seems like this should just be a giant list instead
    #    for component in self._components:
    #        d = component._Magicbot__autosend
    #        for f in d.keys():
    #            d[f] = f(component)     

    def _execute_components(self):
        for component in self._components:
            try:
                component.execute()
            except:
                self.onException()
