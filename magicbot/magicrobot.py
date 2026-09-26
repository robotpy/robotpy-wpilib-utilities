import contextlib
import inspect
import logging
import sys
import types
import typing
from typing import Any, Callable

import hal
import toposort
import wpilib
from ntcore import NetworkTableInstance

from robotpy_ext.autonomous import AutonomousModeSelector
from robotpy_ext.misc import NotifierDelay
from robotpy_ext.misc.simple_watchdog import SimpleWatchdog

from .inject import find_injections, get_injection_requests
from .magic_reset import collect_resets
from .magic_tunable import collect_feedbacks, setup_tunables, tunable

__all__ = ["MagicRobot"]


class MagicInjectError(ValueError):
    pass


class MagicRobot(wpilib.RobotBase):
    """
    Robots that use the MagicBot framework should use this as their
    base robot class. If you use this as your base, you must
    implement the following methods:

    - :meth:`create_objects`
    - :meth:`teleop_periodic`

    MagicRobot uses the :class:`.AutonomousModeSelector` to allow you
    to define multiple autonomous modes and to select one of them via
    the SmartDashboard.

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

    #: If True, teleop_periodic will be called in autonomous mode
    use_teleop_in_autonomous = False

    def __init__(self) -> None:
        super().__init__()
        hal.report_usage("Framework", "Magicbot")

        self._exclude_from_injection = ["logger"]

        self.__last_error_report = -10.0

        self._components: list[tuple[str, Any]] = []
        self._feedbacks: list[tuple[Callable[[], Any], Callable[[Any], Any]]] = []
        self._reset_components: list[tuple[dict[str, Any], Any]] = []

        self.__done = False

        # cache these
        self.__is_ds_attached = wpilib.RobotState.is_ds_attached
        self.__sd_update = wpilib.SmartDashboard.update_values

    def simulation_init(self) -> None:
        """Robot-wide simulation initialization code should go here.

        Users should override this method for default Robot-wide simulation
        related initialization which will be called when the robot is first
        started. It will be called exactly one time after the robot class
        constructor is called only when the robot is in simulation.
        """
        pass

    def simulation_periodic(self) -> None:
        """Periodic simulation code should go here.

        This function is called in a simulated robot after user code executes.
        """
        pass

    def __simulation_periodic(self) -> None:
        hal.sim_periodic_before()
        self.simulation_periodic()
        hal.sim_periodic_after()

    def robot_init(self) -> None:
        """
        .. warning:: Internal API, don't override; use :meth:`create_objects` instead
        """

        # Create the user's objects and stuff here
        self.create_objects()

        # Load autonomous modes
        self._automodes = AutonomousModeSelector("autonomous")

        # Next, create the robot components and wire them together
        self._create_components()

        self.__nt = NetworkTableInstance.get_default().get_table("/robot")

        self.__nt_put_is_ds_attached = self.__nt.get_entry("is_ds_attached").set_boolean
        self.__nt_put_mode = self.__nt.get_entry("mode").set_string

        self.__nt.put_boolean("is_simulation", self.is_simulation())
        self.__nt_put_is_ds_attached(self.__is_ds_attached())

        self.watchdog = SimpleWatchdog(self.control_loop_wait_time)

        self.__periodics: list[tuple[Callable[[], None], str]] = [
            (self.robot_periodic, "robot_periodic()"),
        ]

        if self.is_simulation():
            self.simulation_init()
            self.__periodics.append(
                (self.__simulation_periodic, "simulation_periodic()")
            )

    def create_objects(self) -> None:
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

    def autonomous_init(self) -> None:
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

    def teleop_init(self) -> None:
        """
        Initialization code for teleop control code may go here.

        Users may override this method for initialization code which will be
        called each time the robot enters teleop mode.

        .. note:: The ``on_enable`` functions of all components are called
                  before this function is called.
        """
        pass

    def teleop_periodic(self):
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
        func = self.teleop_periodic.__func__
        if not hasattr(func, "firstRun"):
            self.logger.warning(
                "Default MagicRobot.teleop_periodic() method... Override me!"
            )
            func.firstRun = False

    def disabled_init(self) -> None:
        """
        Initialization code for disabled mode may go here.

        Users may override this method for initialization code which will be
        called each time the robot enters disabled mode.

        .. note:: The ``on_disable`` functions of all components are called
                  before this function is called.
        """
        pass

    def disabled_periodic(self):
        """
        Periodic code for disabled mode should go here.

        Users should override this method for code which will be called
        periodically at a regular rate while the robot is in disabled mode.

        This code executes before the ``execute`` functions of all
        components are called.
        """
        func = self.disabled_periodic.__func__
        if not hasattr(func, "firstRun"):
            self.logger.warning(
                "Default MagicRobot.disabled_periodic() method... Override me!"
            )
            func.firstRun = False

    def utility_init(self) -> None:
        """Initialization code for utility mode should go here.

        Users should override this method for initialization code which will be
        called each time the robot enters utility mode.
        """
        pass

    def utility_periodic(self) -> None:
        """Periodic code for utility mode should go here."""
        pass

    def robot_periodic(self) -> None:
        """
        Periodic code for all modes should go here.

        Users must override this method to utilize it
        but it is not required.

        This function gets called last in each mode.
        You may use it for any code you need to run
        during all modes of the robot (e.g NetworkTables updates)

        The default implementation will update SmartDashboard
        """
        watchdog = self.watchdog
        self.__sd_update()
        watchdog.add_epoch("SmartDashboard")

    def on_exception(self, force_report: bool = False) -> None:
        """
        This function must *only* be called when an unexpected exception
        has occurred that would otherwise crash the robot code. Use this
        inside your :meth:`teleop_periodic` function.

        If the FMS is attached (e.g. during a real competition match),
        this function will return without raising an error. However,
        it will try to report one-off errors to the Driver Station so
        that it will be recorded in the Driver Station log.
        Repeated errors may not get logged.

        Example usage::

            def teleop_periodic(self):
                try:
                    if self.joystick.get_trigger():
                        self.shooter.shoot()
                except:
                    self.on_exception()

                try:
                    if self.gamepad.get_left_bumper_button():
                        self.ball_intake.run()
                except:
                    self.on_exception()

                # and so on...

        :param force_report: Always report the exception to the DS. Don't
                             set this to True
        """
        # If the FMS is not attached, crash the robot program
        if not wpilib.RobotState.is_fms_attached():
            raise

        # Otherwise, if the FMS is attached then try to report the error via
        # the driver station console. Maybe.
        now = wpilib.Timer.get_timestamp()

        try:
            if (
                force_report
                or (now - self.__last_error_report) > self.error_report_interval
            ):
                wpilib.report_error("Unexpected exception", True)
        except:
            pass  # ok, can't do anything here

        self.__last_error_report = now

    @contextlib.contextmanager
    def consume_exceptions(self, force_report: bool = False):
        """
        This returns a context manager which will consume any uncaught
        exceptions that might otherwise crash the robot.

        Example usage::

            def teleop_periodic(self):
                with self.consume_exceptions():
                    if self.joystick.get_trigger():
                        self.shooter.shoot()

                with self.consume_exceptions():
                    if self.gamepad.get_left_bumper_button():
                        self.ball_intake.run()

                # and so on...

        :param force_report: Always report the exception to the DS. Don't
                             set this to True

        .. seealso:: :meth:`on_exception` for more details
        """
        try:
            yield
        except:
            self.on_exception(force_report=force_report)

    #
    # Internal API
    #

    def start_competition(self) -> None:
        """
        This runs the mode-switching loop.

        .. warning:: Internal API, don't override
        """

        self.robot_init()

        # Tell the DS the robot is ready to be enabled
        hal.observe_user_program_starting()

        while not self.__done:
            word = wpilib.DriverStationBackend.get_control_word()

            if not word.is_enabled():
                self._disabled()
            elif word.is_autonomous():
                self.autonomous()
            elif word.is_utility():
                self._test()
            else:
                self._operator_control()

    def end_competition(self) -> None:
        self.__done = True
        self._automodes.end_competition()

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
            self.autonomous_init()
        except:
            self.on_exception(force_report=True)

        auto_functions: tuple[Callable[[], None], ...] = (self._enabled_periodic,)

        if self.use_teleop_in_autonomous:
            auto_functions = (self.teleop_periodic,) + auto_functions

        self._automodes.run(
            self.control_loop_wait_time,
            auto_functions,
            self.on_exception,
            watchdog=self.watchdog,
        )

    def _disabled(self) -> None:
        """
        This function is called in disabled mode. You should not
        override this function; rather, you should override the
        :meth:`disabled_periodic` function instead.

        .. warning:: Internal API, don't override
        """
        watchdog = self.watchdog
        watchdog.reset()

        self.__nt_put_mode("disabled")
        ds_attached = None

        self._on_mode_disable_components()
        try:
            self.disabled_init()
        except:
            self.on_exception(force_report=True)
        watchdog.add_epoch("disabled_init()")

        refresh_data = wpilib.DriverStationBackend.refresh_data
        DSControlWord = wpilib.DriverStationBackend.get_control_word

        with NotifierDelay(self.control_loop_wait_time) as delay:
            while not self.__done:
                refresh_data()
                cw = DSControlWord()
                if cw.is_enabled():
                    break

                if ds_attached != cw.is_ds_attached():
                    ds_attached = not ds_attached
                    self.__nt_put_is_ds_attached(ds_attached)

                hal.observe_user_program(cw.get_value())
                try:
                    self.disabled_periodic()
                except:
                    self.on_exception()
                watchdog.add_epoch("disabled_periodic()")

                self._do_periodics()
                # watchdog.disable()
                watchdog.print_if_expired()

                delay.wait()
                watchdog.reset()

    def _operator_control(self) -> None:
        """
        This function is called in teleoperated mode. You should not
        override this function; rather, you should override the
        :meth:`teleop_periodic` function instead.

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
            self.teleop_init()
        except:
            self.on_exception(force_report=True)
        watchdog.add_epoch("teleop_init()")

        observe = hal.observe_user_program
        refresh_data = wpilib.DriverStationBackend.refresh_data
        get_control_word = wpilib.DriverStationBackend.get_control_word

        with NotifierDelay(self.control_loop_wait_time) as delay:
            while not self.__done:
                refresh_data()
                word = get_control_word()
                if not word.is_teleop_enabled():
                    break

                observe(word.get_value())
                try:
                    self.teleop_periodic()
                except:
                    self.on_exception()
                watchdog.add_epoch("teleop_periodic()")

                self._enabled_periodic()
                # watchdog.disable()
                watchdog.print_if_expired()

                delay.wait()
                watchdog.reset()

    def _test(self) -> None:
        """Called when the robot is in test mode"""
        watchdog = self.watchdog
        watchdog.reset()

        self.__nt_put_mode("test")
        self.__nt_put_is_ds_attached(self.__is_ds_attached())

        # initialize things
        self._on_mode_enable_components()

        try:
            self.utility_init()
        except:
            self.on_exception(force_report=True)
        watchdog.add_epoch("utility_init()")

        refresh_data = wpilib.DriverStationBackend.refresh_data
        DSControlWord = wpilib.DriverStationBackend.get_control_word

        with NotifierDelay(self.control_loop_wait_time) as delay:
            while not self.__done:
                refresh_data()
                cw = DSControlWord()
                if not cw.is_utility_enabled():
                    break

                hal.observe_user_program(cw.get_value())
                try:
                    self.utility_periodic()
                except:
                    self.on_exception()
                watchdog.add_epoch("utility_periodic()")

                self._do_periodics()
                # watchdog.disable()
                watchdog.print_if_expired()

                delay.wait()
                watchdog.reset()

    def _on_mode_enable_components(self) -> None:
        # initialize things
        for _, component in self._components:
            on_enable = getattr(component, "on_enable", None)
            if on_enable is not None:
                try:
                    on_enable()
                except:
                    self.on_exception(force_report=True)

    def _on_mode_disable_components(self) -> None:
        # deinitialize things
        for _, component in self._components:
            on_disable = getattr(component, "on_disable", None)
            if on_disable is not None:
                try:
                    on_disable()
                except:
                    self.on_exception(force_report=True)

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
                    f"{cls.__name__} has a non-type annotation on {m} ({ctyp!r}); lone non-injection variable annotations are disallowed, did you want to assign a static variable?"
                )

            component = self._create_component(m, ctyp, injectables)

            # Store for later
            components.append((m, component))
            injectables[m] = component

        # Sort components so that setup functions can rely on the setup of an
        # injected variable being called already
        component_by_id = {id(component): cname for cname, component in components}

        dag = {}
        for cname, component in components:
            setup = getattr(component, "setup", None)
            if setup is None:
                dag[cname] = []
            else:
                type_hints = typing.get_type_hints(type(component))
                requests = get_injection_requests(type_hints, cname, component)

                deps = []
                for n in requests:
                    injectable = injectables.get(n)
                    if injectable is None:
                        injectable = injectables.get(f"{cname}_{n}")

                    # Only include dependencies that are other magic components.
                    # This keeps toposort nodes aligned with `components` and
                    # ignores scalar/robot-level injectables (ex: config values).
                    dep_name = component_by_id.get(id(injectable))
                    if dep_name is not None:
                        deps.append(dep_name)

                dag[cname] = deps

        # Create an ordered component list based on possible setup() dependencies
        setup_ordered_components = [
            (cname, injectables[cname])
            for cname in list(toposort.toposort_flatten(dag))
        ]

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
        # This is the one time we call the components out of declaration order
        # so that dependencies within them don't break
        for cname, component in setup_ordered_components:
            setup = getattr(component, "setup", None)
            if setup is not None:
                setup()

        # Grab all the feedback methods
        for cname, component in components:
            self._feedbacks += collect_feedbacks(component, cname, "components")

        # Call setup functions for autonomous modes
        for mode in self._automodes.modes.values():
            if hasattr(mode, "setup"):
                mode.setup()

        self._components = components

    def _collect_injectables(self) -> dict[str, Any]:
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

    def _create_component(self, name: str, ctyp: type, injectables: dict[str, Any]):
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
                f"Component {name} ({component!r}) must have a method named 'execute'"
            )

        # Automatically inject a logger object
        component.logger = logging.getLogger(name)

        self.logger.info("-> %s (class: %s)", name, ctyp.__name__)

        return component

    def _setup_vars(self, cname: str, component, injectables: dict[str, Any]) -> None:
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
                self.on_exception()
            else:
                setter(value)

        watchdog.add_epoch("@magicbot.feedback")

        for periodic, name in self.__periodics:
            periodic()
            watchdog.add_epoch(name)

        for reset_dict, component in self._reset_components:
            component.__dict__.update(reset_dict)

    def _enabled_periodic(self) -> None:
        """Run components and all periodic methods."""
        watchdog = self.watchdog

        for name, component in self._components:
            try:
                component.execute()
            except:
                self.on_exception()
            watchdog.add_epoch(name)

        self._do_periodics()
