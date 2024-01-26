import contextlib
import inspect
import logging
import sys
import types
import typing

from typing import Any, Callable, Dict, List, Tuple

import hal
import wpilib

from ntcore import NetworkTableInstance

# from wpilib.shuffleboard import Shuffleboard

from robotpy_ext.autonomous import AutonomousModeSelector
from robotpy_ext.misc import NotifierDelay
from robotpy_ext.misc.simple_watchdog import SimpleWatchdog

from .inject import get_injection_requests, find_injections
from .magic_tunable import setup_tunables, tunable, collect_feedbacks
from .magic_reset import collect_resets

__all__ = ["MagicRobot"]


class MagicInjectError(ValueError):
    pass


class MagicRobot(wpilib.RobotBase):
    """
    Robots that use the MagicBot framework should use this as their
    base robot class. If you use this as your base, you must
    implement the following methods:

    - :meth:`createObjects`
    - :meth:`teleopPeriodic`

    MagicRobot uses the :class:`.AutonomousModeSelector` to allow you
    to define multiple autonomous modes and to select one of them via
    the SmartDashboard/Shuffleboard.

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

    #: A Python logging object that you can use to send messages to the log.
    #: It is recommended to use this instead of print statements.
    logger = logging.getLogger("robot")

    #: If True, teleopPeriodic will be called in autonomous mode
    use_teleop_in_autonomous = False

    def __init__(self) -> None:
        super().__init__()

        self._exclude_from_injection = ["logger"]

        self.__last_error_report = -10

        self._components: List[Tuple[str, Any]] = []
        self._feedbacks: List[Tuple[Callable[[], Any], Callable[[Any], Any]]] = []
        self._reset_components: List[Tuple[Dict[str, Any], Any]] = []

        self.__done = False

        # cache these
        self.__is_ds_attached = wpilib.DriverStation.isDSAttached
        self.__sd_update = wpilib.SmartDashboard.updateValues
        self.__lv_update = wpilib.LiveWindow.updateValues
        # self.__sf_update = Shuffleboard.update

    def _simulationInit(self) -> None:
        pass

    def _simulationPeriodic(self) -> None:
        pass

    def __simulationPeriodic(self) -> None:
        hal.simPeriodicBefore()
        self._simulationPeriodic()
        hal.simPeriodicAfter()

    def robotInit(self) -> None:
        """
        .. warning:: Internal API, don't override; use :meth:`createObjects` instead
        """

        # Create the user's objects and stuff here
        self.createObjects()

        # Load autonomous modes
        self._automodes = AutonomousModeSelector("autonomous")

        # Next, create the robot components and wire them together
        self._create_components()

        # cache these
        self.__is_ds_attached = wpilib.DriverStation.isDSAttached
        self.__sd_update = wpilib.SmartDashboard.updateValues
        self.__lv_update = wpilib.LiveWindow.updateValues
        # self.__sf_update = Shuffleboard.update

        self.__nt = NetworkTableInstance.getDefault().getTable("/robot")

        self.__nt_put_is_ds_attached = self.__nt.getEntry("is_ds_attached").setBoolean
        self.__nt_put_mode = self.__nt.getEntry("mode").setString

        self.__nt.putBoolean("is_simulation", self.isSimulation())
        self.__nt_put_is_ds_attached(self.__is_ds_attached())

        self.watchdog = SimpleWatchdog(self.control_loop_wait_time)

        self.__periodics: List[Tuple[Callable[[], None], str]] = [
            (self.robotPeriodic, "robotPeriodic()"),
        ]

        if self.isSimulation():
            self._simulationInit()
            self.__periodics.append((self.__simulationPeriodic, "simulationPeriodic()"))

    def createObjects(self) -> None:
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

    def autonomousInit(self) -> None:
        """Initialization code for autonomous mode may go here.

        Users may override this method for initialization code which
        will be called each time the robot enters autonomous mode,
        regardless of the selected autonomous mode.

        This can be useful for code that must be run at the beginning of a match.

        .. note::

           This method is called after every component's ``on_enable`` method,
           but before the selected autonomous mode's ``on_enable`` method.
        """
        pass

    def teleopInit(self) -> None:
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

        .. note:: If you want this function to be called in autonomous
                  mode, set ``use_teleop_in_autonomous`` to True in your
                  robot class.
        """
        func = self.teleopPeriodic.__func__
        if not hasattr(func, "firstRun"):
            self.logger.warning(
                "Default MagicRobot.teleopPeriodic() method... Override me!"
            )
            func.firstRun = False

    def disabledInit(self) -> None:
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
            self.logger.warning(
                "Default MagicRobot.disabledPeriodic() method... Override me!"
            )
            func.firstRun = False

    def testInit(self) -> None:
        """Initialization code for test mode should go here.

        Users should override this method for initialization code which will be
        called each time the robot enters disabled mode.
        """
        pass

    def testPeriodic(self) -> None:
        """Periodic code for test mode should go here."""
        pass

    def robotPeriodic(self) -> None:
        """
        Periodic code for all modes should go here.

        Users must override this method to utilize it
        but it is not required.

        This function gets called last in each mode.
        You may use it for any code you need to run
        during all modes of the robot (e.g NetworkTables updates)

        The default implementation will update
        SmartDashboard, LiveWindow and Shuffleboard.
        """
        watchdog = self.watchdog
        self.__sd_update()
        watchdog.addEpoch("SmartDashboard")
        self.__lv_update()
        watchdog.addEpoch("LiveWindow")
        # self.__sf_update()
        # watchdog.addEpoch("Shuffleboard")

    def onException(self, forceReport: bool = False) -> None:
        """
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
        """
        # If the FMS is not attached, crash the robot program
        if not wpilib.DriverStation.isFMSAttached():
            raise

        # Otherwise, if the FMS is attached then try to report the error via
        # the driver station console. Maybe.
        now = wpilib.Timer.getFPGATimestamp()

        try:
            if (
                forceReport
                or (now - self.__last_error_report) > self.error_report_interval
            ):
                wpilib.reportError("Unexpected exception", True)
        except:
            pass  # ok, can't do anything here

        self.__last_error_report = now

    @contextlib.contextmanager
    def consumeExceptions(self, forceReport: bool = False):
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

    def startCompetition(self) -> None:
        """
        This runs the mode-switching loop.

        .. warning:: Internal API, don't override
        """

        # TODO: usage reporting?
        self.robotInit()

        # Tell the DS the robot is ready to be enabled
        hal.observeUserProgramStarting()

        while not self.__done:
            isEnabled, isAutonomous, isTest = self.getControlState()

            if not isEnabled:
                self._disabled()
            elif isAutonomous:
                self.autonomous()
            elif isTest:
                self._test()
            else:
                self._operatorControl()

    def endCompetition(self) -> None:
        self.__done = True
        self._automodes.endCompetition()

    def autonomous(self) -> None:
        """
        MagicRobot will do The Right Thing and automatically load all
        autonomous mode routines defined in the autonomous folder.

        .. warning:: Internal API, don't override
        """

        self.__nt_put_mode("auto")
        self.__nt_put_is_ds_attached(self.__is_ds_attached())

        self._on_mode_enable_components()

        try:
            self.autonomousInit()
        except:
            self.onException(forceReport=True)

        auto_functions: Tuple[Callable[[], None], ...] = (self._enabled_periodic,)

        if self.use_teleop_in_autonomous:
            auto_functions = (self.teleopPeriodic,) + auto_functions

        self._automodes.run(
            self.control_loop_wait_time,
            auto_functions,
            self.onException,
            watchdog=self.watchdog,
        )

        self._on_mode_disable_components()

    def _disabled(self) -> None:
        """
        This function is called in disabled mode. You should not
        override this function; rather, you should override the
        :meth:`disabledPeriodic` function instead.

        .. warning:: Internal API, don't override
        """
        watchdog = self.watchdog
        watchdog.reset()

        self.__nt_put_mode("disabled")
        ds_attached = None

        self._on_mode_disable_components()
        try:
            self.disabledInit()
        except:
            self.onException(forceReport=True)
        watchdog.addEpoch("disabledInit()")

        refreshData = wpilib.DriverStation.refreshData
        DSControlWord = wpilib.DSControlWord

        with NotifierDelay(self.control_loop_wait_time) as delay:
            while not self.__done:
                refreshData()
                cw = DSControlWord()
                if cw.isEnabled():
                    break

                if ds_attached != cw.isDSAttached():
                    ds_attached = not ds_attached
                    self.__nt_put_is_ds_attached(ds_attached)

                hal.observeUserProgramDisabled()
                try:
                    self.disabledPeriodic()
                except:
                    self.onException()
                watchdog.addEpoch("disabledPeriodic()")

                self._do_periodics()
                # watchdog.disable()
                watchdog.printIfExpired()

                delay.wait()
                watchdog.reset()

    def _operatorControl(self) -> None:
        """
        This function is called in teleoperated mode. You should not
        override this function; rather, you should override the
        :meth:`teleopPeriodics` function instead.

        .. warning:: Internal API, don't override
        """
        watchdog = self.watchdog
        watchdog.reset()

        self.__nt_put_mode("teleop")
        # don't need to update this during teleop -- presumably will switch
        # modes when ds is no longer attached
        self.__nt_put_is_ds_attached(self.__is_ds_attached())

        # initialize things
        self._on_mode_enable_components()

        try:
            self.teleopInit()
        except:
            self.onException(forceReport=True)
        watchdog.addEpoch("teleopInit()")

        observe = hal.observeUserProgramTeleop
        refreshData = wpilib.DriverStation.refreshData
        isTeleopEnabled = wpilib.DriverStation.isTeleopEnabled

        with NotifierDelay(self.control_loop_wait_time) as delay:
            while not self.__done:
                refreshData()
                if not isTeleopEnabled():
                    break

                observe()
                try:
                    self.teleopPeriodic()
                except:
                    self.onException()
                watchdog.addEpoch("teleopPeriodic()")

                self._enabled_periodic()
                # watchdog.disable()
                watchdog.printIfExpired()

                delay.wait()
                watchdog.reset()

        self._on_mode_disable_components()

    def _test(self) -> None:
        """Called when the robot is in test mode"""
        watchdog = self.watchdog
        watchdog.reset()

        self.__nt_put_mode("test")
        self.__nt_put_is_ds_attached(self.__is_ds_attached())

        wpilib.LiveWindow.setEnabled(True)
        # Shuffleboard.enableActuatorWidgets()

        try:
            self.testInit()
        except:
            self.onException(forceReport=True)
        watchdog.addEpoch("testInit()")

        refreshData = wpilib.DriverStation.refreshData
        DSControlWord = wpilib.DSControlWord

        with NotifierDelay(self.control_loop_wait_time) as delay:
            while not self.__done:
                refreshData()
                cw = DSControlWord()
                if not (cw.isTest() and cw.isEnabled()):
                    break

                hal.observeUserProgramTest()
                try:
                    self.testPeriodic()
                except:
                    self.onException()
                watchdog.addEpoch("testPeriodic()")

                self._do_periodics()
                # watchdog.disable()
                watchdog.printIfExpired()

                delay.wait()
                watchdog.reset()

        wpilib.LiveWindow.setEnabled(False)
        # Shuffleboard.disableActuatorWidgets()

    def _on_mode_enable_components(self) -> None:
        # initialize things
        for _, component in self._components:
            on_enable = getattr(component, "on_enable", None)
            if on_enable is not None:
                try:
                    on_enable()
                except:
                    self.onException(forceReport=True)

    def _on_mode_disable_components(self) -> None:
        # deinitialize things
        for _, component in self._components:
            on_disable = getattr(component, "on_disable", None)
            if on_disable is not None:
                try:
                    on_disable()
                except:
                    self.onException(forceReport=True)

    def _create_components(self) -> None:
        #
        # TODO: Will need to inject into any autonomous mode component
        #       too, as they're a bit different
        #

        # TODO: Will need to order state machine components before
        #       other components just in case

        components = []

        self.logger.info("Creating magic components")

        # Identify all of the types, and create them
        cls = type(self)

        # - Iterate over class variables with type annotations
        # .. this hack is necessary for pybind11 based modules
        sys.modules["pybind11_builtins"] = types.SimpleNamespace()  # type: ignore

        injectables = self._collect_injectables()

        for m, ctyp in typing.get_type_hints(cls).items():
            # Ignore private variables
            if m.startswith("_"):
                continue

            # If the variable has been set, skip it
            if hasattr(self, m):
                continue

            # If the type is not actually a type, give a meaningful error
            if not isinstance(ctyp, type):
                raise TypeError(
                    "%s has a non-type annotation on %s (%r); lone non-injection variable annotations are disallowed, did you want to assign a static variable?"
                    % (cls.__name__, m, ctyp)
                )

            component = self._create_component(m, ctyp, injectables)

            # Store for later
            components.append((m, component))
            injectables[m] = component

        # For each new component, perform magic injection
        for cname, component in components:
            setup_tunables(component, cname, "components")
            self._setup_vars(cname, component, injectables)
            self._setup_reset_vars(component)

        # Do it for autonomous modes too
        for mode in self._automodes.modes.values():
            mode.logger = logging.getLogger(mode.MODE_NAME)
            setup_tunables(mode, mode.MODE_NAME, "autonomous")
            self._setup_vars(mode.MODE_NAME, mode, injectables)

        # And for self too
        setup_tunables(self, "robot", None)
        self._feedbacks += collect_feedbacks(self, "robot", None)

        # Call setup functions for components
        for cname, component in components:
            setup = getattr(component, "setup", None)
            if setup is not None:
                setup()
            # ... and grab all the feedback methods
            self._feedbacks += collect_feedbacks(component, cname, "components")

        # Call setup functions for autonomous modes
        for mode in self._automodes.modes.values():
            if hasattr(mode, "setup"):
                mode.setup()

        self._components = components

    def _collect_injectables(self) -> Dict[str, Any]:
        injectables = {}
        cls = type(self)

        for n in dir(self):
            if (
                n.startswith("_")
                or n in self._exclude_from_injection
                or isinstance(getattr(cls, n, None), (property, tunable))
            ):
                continue

            o = getattr(self, n)

            # Don't inject methods
            # TODO: This could actually be a cool capability..
            if inspect.ismethod(o):
                continue

            injectables[n] = o

        return injectables

    def _create_component(self, name: str, ctyp: type, injectables: Dict[str, Any]):
        type_hints = typing.get_type_hints(ctyp.__init__)
        NoneType = type(None)
        init_return_type = type_hints.pop("return", NoneType)
        assert (
            init_return_type is NoneType
        ), f"{ctyp!r} __init__ had an unexpected non-None return type hint"
        requests = get_injection_requests(type_hints, name)
        injections = find_injections(requests, injectables, name)

        # Create instance, set it on self
        component = ctyp(**injections)
        setattr(self, name, component)

        # Ensure that mandatory methods are there
        if not callable(getattr(component, "execute", None)):
            raise ValueError(
                "Component %s (%r) must have a method named 'execute'"
                % (name, component)
            )

        # Automatically inject a logger object
        component.logger = logging.getLogger(name)

        self.logger.info("-> %s (class: %s)", name, ctyp.__name__)

        return component

    def _setup_vars(self, cname: str, component, injectables: Dict[str, Any]) -> None:
        self.logger.debug("Injecting magic variables into %s", cname)

        type_hints = typing.get_type_hints(type(component))
        requests = get_injection_requests(type_hints, cname, component)
        injections = find_injections(requests, injectables, cname)
        component.__dict__.update(injections)

    def _setup_reset_vars(self, component) -> None:
        reset_dict = collect_resets(type(component))

        if reset_dict:
            component.__dict__.update(reset_dict)
            self._reset_components.append((reset_dict, component))

    def _do_periodics(self) -> None:
        """Run periodic methods which run in every mode."""
        watchdog = self.watchdog

        for method, setter in self._feedbacks:
            try:
                value = method()
            except:
                self.onException()
            else:
                setter(value)

        watchdog.addEpoch("@magicbot.feedback")

        for periodic, name in self.__periodics:
            periodic()
            watchdog.addEpoch(name)

    def _enabled_periodic(self) -> None:
        """Run components and all periodic methods."""
        watchdog = self.watchdog

        for name, component in self._components:
            try:
                component.execute()
            except:
                self.onException()
            watchdog.addEpoch(name)

        self._do_periodics()

        for reset_dict, component in self._reset_components:
            component.__dict__.update(reset_dict)
