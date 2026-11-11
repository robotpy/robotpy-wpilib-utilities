import contextlib
import inspect
import logging
import sys
import types
import typing
from collections.abc import Callable
from pathlib import Path
from typing import Any

import hal
import toposort
import tunables
import wpilib
import wpiutil
from ntcore import NetworkTableInstance

from robotpy_ext.misc import NotifierDelay
from robotpy_ext.misc.simple_watchdog import SimpleWatchdog

from .inject import find_injections, get_injection_requests
from .magic_reset import collect_resets
from .magic_tunable import collect_feedbacks, setup_tunables, tunable

__all__ = ["MagicRobot"]


class MagicInjectError(ValueError):
    pass


_MODE_NAMES = {
    hal.RobotMode.AUTONOMOUS: "auto",
    hal.RobotMode.TELEOPERATED: "teleop",
    hal.RobotMode.UTILITY: "utility",
}


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

    - ``/robot/mode``: one of 'disabled', 'auto', 'teleop', or 'utility'
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

    #: If True, decorated OpModes are automatically discovered, registered,
    #: and published to the Driver Station
    opmode_auto_discover = True

    def __init__(self) -> None:
        super().__init__()
        hal.report_usage("Framework", "Magicbot")

        self._exclude_from_injection = ["logger"]

        self.__last_error_report = -10.0

        self._components: list[tuple[str, Any]] = []
        self._feedbacks: list[tuple[Callable[[], Any], Callable[[Any], Any]]] = []
        self._reset_components: list[tuple[dict[str, Any], Any]] = []

        # opmode id -> (name, class)
        self.__opmodes: dict[int, tuple[str, type]] = {}

        # opmode lifecycle state
        self.__last_mode_id = -1
        self.__last_enabled_state = False

        self.__opmode: wpilib.OpMode | None = None
        self.__opmode_name = ""
        self.__opmode_started = False
        self.__opmode_injectables: dict[str, Any] = {}

        self.__done = False

        # cache these
        self.__is_ds_attached = wpilib.RobotState.is_ds_attached
        self.__tunables_update = tunables.TunableRegistry.update

    def simulation_init(self) -> None:
        """Robot-wide simulation initialization code should go here.

        Users should override this method for default Robot-wide simulation
        related initialization which will be called when the robot is first
        started. It will be called exactly one time after the robot class
        constructor is called only when the robot is in simulation.
        """

    def simulation_periodic(self) -> None:
        """Periodic simulation code should go here.

        This function is called in a simulated robot after user code executes.
        """

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

        # Next, create the robot components and wire them together
        self._create_components()

        # Register the OpModes and make them visible to the driver station
        if self.opmode_auto_discover:
            self._discover_opmodes()
        self.publish_opmodes()

        self.__nt = NetworkTableInstance.get_default().get_table("/robot")

        self.__nt_put_is_ds_attached = self.__nt.get_entry("is_ds_attached").set_boolean
        self.__nt_put_mode = self.__nt.get_entry("mode").set_string
        self.__nt_put_opmode = self.__nt.get_entry("opmode").set_string

        self.__nt.put_boolean("is_simulation", self.is_simulation())
        self.__nt_put_is_ds_attached(self.__is_ds_attached())
        self.__nt_put_mode("disabled")
        self.__nt_put_opmode("")

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

    def disabled_init(self) -> None:
        """
        Initialization code for disabled mode may go here.

        Users may override this method for initialization code which will be
        called each time the robot enters disabled mode.

        .. note:: The ``on_disable`` functions of all components are called
                  before this function is called.
        """

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

    def disabled_exit(self) -> None:
        """
        Code that runs once when the robot exits disabled mode may go here.

        This is called before the selected OpMode is started.
        """

    def none_periodic(self) -> None:
        """
        Periodic code for when no OpMode is selected may go here.

        This is called periodically at a regular rate while no OpMode is
        selected, including when the Driver Station is disconnected.
        """

    def driver_station_connected(self) -> None:
        """
        Code that needs to know the DS state should go here.

        Users may override this method for initialization that needs to occur
        after the DS is connected, such as needing the alliance information.
        This is called once, when the DS first connects.
        """

    def robot_periodic(self) -> None:
        """
        Periodic code for all modes should go here.

        Users must override this method to utilize it
        but it is not required.

        This function gets called last in each mode.
        You may use it for any code you need to run
        during all modes of the robot (e.g NetworkTables updates)

        The default implementation will update WPILib's Tunables
        (Not to be confused with Magicbot's which auto updates)
        """
        watchdog = self.watchdog
        self.__tunables_update()
        watchdog.add_epoch("TunableRegistry.update()")

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

        with NotifierDelay(self.control_loop_wait_time) as delay:
            while not self.__done:
                self._loop_func()
                delay.wait()

    def end_competition(self) -> None:
        self.__done = True

    def _loop_func(self):
        watchdog = self.watchdog
        watchdog.reset()

        wpilib.DriverStationBackend.refresh_data()
        word = wpilib.DriverStationBackend.get_control_word()

        enabled = word.is_enabled()
        ds_attached = word.is_ds_attached()
        mode_id = word.get_opmode_id() if ds_attached else 0

        mode_changed = mode_id != self.__last_mode_id
        self.__last_mode_id = mode_id

        # Opmode change
        if mode_changed and self.__opmode:
            self._end_opmode()

        # setup new opmode
        just_created_opmode = False
        if mode_changed and mode_id != 0 and self.__opmode is None:
            entry = self.__opmodes.get(mode_id)
            if entry is None:
                wpilib.report_error(f"No opmodes found for mode {mode_id}")
            else:
                opmode = self._create_opmode(*entry)
                if opmode is not None:
                    self.__opmode_disabled_periodic(opmode)
                    just_created_opmode = True

        just_called_disabled_init = False
        if self.__last_enabled_state != enabled:
            if enabled:
                self.disabled_exit()
                watchdog.add_epoch("disabled_exit()")
            else:
                # Transitioning to disabled. Only tear down an opmode that was actually
                # running; a freshly selected opmode entering its disabled phase must
                # persist so it can be started on the next enable.
                if self.__opmode is not None:
                    self._end_opmode()
                    self.__last_mode_id = -1
                self.disabled_init()
                watchdog.add_epoch("disabled_init()")
            self.__last_enabled_state = enabled

        # Start the opmode if enabled and not already started. This single check
        # covers both the disabled->enabled transition and an opmode constructed
        # while the robot is already enabled.
        opmode = self.__opmode
        if enabled and opmode is not None and not self.__opmode_started:
            self._start_opmode(opmode, word.get_robot_mode())

        opmode = self.__opmode
        if opmode is not None and self.__opmode_started:
            try:
                opmode.periodic()
            except:
                self.on_exception()
            watchdog.add_epoch("opmode.periodic()")

            self._enabled_periodic()
        else:
            if not enabled:
                if not just_called_disabled_init:
                    try:
                        self.disabled_periodic()
                    except:
                        self.on_exception()
                    watchdog.add_epoch("disabled_periodic()")

                if opmode is not None and not just_created_opmode:
                    self.__opmode_disabled_periodic(opmode)

            if mode_id == 0:
                try:
                    self.none_periodic()
                except:
                    self.on_exception()
                watchdog.add_epoch("none_periodic()")

            self._do_periodics()

        hal.observe_user_program(word.get_value())

        # watchdog.disable()
        watchdog.print_if_expired()

    def _start_opmode(self, opmode: wpilib.OpMode, robot_mode: hal.RobotMode) -> None:
        self.logger.info("Starting OpMode %s", self.__opmode_name)

        self.__nt_put_mode(_MODE_NAMES.get(robot_mode, "unknown"))
        self.__nt_put_opmode(self.__opmode_name)
        self.__nt_put_is_ds_attached(self.__is_ds_attached())

        self.__opmode_started = True

        # initialize things
        self._on_mode_enable_components()
        self.watchdog.add_epoch("on_enable")

        try:
            opmode.start()
        except:
            self.on_exception(force_report=True)
        self.watchdog.add_epoch("opmode.start()")

    def _end_opmode(self) -> None:
        opmode = self.__opmode
        name = self.__opmode_name
        if opmode is None:
            return

        # If the opmode was started, end it
        if self.__opmode_started:
            self.logger.info("Ending OpMode %s", name)
            try:
                opmode.end()
            except:
                self.on_exception(force_report=True)
            self.watchdog.add_epoch("opmode.end()")

        # regardless of whether the opmode was started, discard it
        self.__opmode = None
        self.__opmode_name = ""
        self.__opmode_started = False
        self.__nt_put_opmode("")

        close = getattr(opmode, "close", None)
        if close is not None:
            try:
                close()
            except:
                self.on_exception(force_report=True)

    def _create_opmode(self, name: str, opmode_cls: type) -> wpilib.OpMode | None:
        """Creates an opmode instance and performs magic injection on it"""
        self.logger.info("Creating OpMode %s", name)

        injectables = self.__opmode_injectables

        try:
            # inject __init__ parameters, if the user defined __init__
            init = opmode_cls.__init__
            if inspect.isfunction(init):
                type_hints = typing.get_type_hints(init)
                type_hints.pop("return", None)
                requests = get_injection_requests(type_hints, name)
                injections = find_injections(requests, injectables, name)
            else:
                injections = {}

            opmode = opmode_cls(**injections)

            # inject class variable annotations
            opmode.logger = logging.getLogger(name)
            self._setup_vars(name, opmode, injectables)
            setup_tunables(opmode, name, "opmodes")

            setup = getattr(opmode, "setup", None)
            if setup is not None:
                setup()

            if opmode.get_callbacks():
                self.logger.warning(
                    "OpMode %s has periodic callbacks, which MagicRobot does not run",
                    name,
                )
        except:
            self.on_exception(force_report=True)
            return None
        finally:
            self.watchdog.add_epoch("opmode create")

        self.__opmode = opmode
        self.__opmode_name = name
        self.__opmode_started = False
        return opmode

    def __opmode_disabled_periodic(self, opmode: wpilib.OpMode) -> None:
        try:
            opmode.disabled_periodic()
        except:
            self.on_exception()
        self.watchdog.add_epoch("opmode.disabled_periodic()")

    def add_opmode(
        self,
        opmode_cls: type,
        mode: hal.RobotMode,
        name: str = "",
        group: str = "",
        description: str = "",
        text_color: wpiutil.Color | None = None,
        background_color: wpiutil.Color | None = None,
    ) -> None:
        """
        Adds an operating mode option. It's necessary to call
        :meth:`publish_opmodes` to make the added modes visible to the
        driver station. If you call this from :meth:`create_objects`, the
        modes are published for you.

        The OpMode is constructed each time it is selected on the driver
        station. Its ``__init__`` parameters and class variable annotations
        are injected the same way as for components.

        The text_color and background_color parameters are optional, but
        setting only one has no effect.

        :param opmode_cls: OpMode class; must be a subclass of :class:`wpilib.OpMode`
        :param mode: robot mode
        :param name: name of the operating mode; defaults to the class name
        :param group: group of the operating mode
        :param description: description of the operating mode
        :param text_color: text color
        :param background_color: background color
        """
        if not inspect.isclass(opmode_cls) or not issubclass(opmode_cls, wpilib.OpMode):
            raise TypeError(f"{opmode_cls!r} is not a subclass of wpilib.OpMode")

        if not name:
            name = opmode_cls.__name__

        if text_color is None or background_color is None:
            opmode_id = wpilib.RobotState.add_opmode(mode, name, group, description)
        else:
            opmode_id = wpilib.RobotState.add_opmode(
                mode, name, group, description, text_color, background_color
            )

        if opmode_id == 0:
            wpilib.report_error(
                f"Error adding OpMode {opmode_cls.__name__}: duplicate name {name!r}"
            )
            return

        self.__opmodes[opmode_id] = (name, opmode_cls)
        self.logger.info(
            "-> OpMode %s (%s, class: %s)", name, mode.name, opmode_cls.__name__
        )
        self.publish_opmodes()

    def remove_opmode(self, mode: hal.RobotMode, name: str) -> None:
        """
        Removes an operating mode option. It's necessary to call
        :meth:`publish_opmodes` to make the removed mode no longer visible
        to the driver station.

        :param mode: robot mode
        :param name: name of the operating mode
        """
        opmode_id = wpilib.RobotState.remove_opmode(mode, name)
        if opmode_id != 0:
            self.__opmodes.pop(opmode_id, None)

    def publish_opmodes(self) -> None:
        """Publishes the operating mode options to the driver station."""
        wpilib.RobotState.publish_opmodes()

    def clear_opmodes(self) -> None:
        """
        Clears all operating mode options and publishes an empty list to
        the driver station.
        """
        wpilib.RobotState.clear_opmodes()
        self.__opmodes.clear()

    def _discover_opmodes(self) -> None:
        """
        Registers all decorated opmodes, importing the ``opmodes`` package
        next to the robot module first. Discovery works the same way as
        :class:`wpilib.OpModeRobot`.
        """
        from wpilib._impl import opmode as _wpi_opmode

        try:
            robot_source = Path(inspect.getfile(type(self)))
        except (TypeError, OSError):
            robot_source = None

        if robot_source is not None:
            package_dir = robot_source.parent / "opmodes"
            if package_dir.is_dir():
                robot_module = type(self).__module__
                robot_package = (
                    robot_module
                    if robot_source.name == "__init__.py"
                    else robot_module.rpartition(".")[0]
                )
                package_name = (
                    f"{robot_package}.opmodes" if robot_package else "opmodes"
                )
                modules = _wpi_opmode._scan_modules(package_dir, package_name)
                _wpi_opmode._import_candidates(modules, package_dir, package_name)

        registered = {cls for _, cls in self.__opmodes.values()}

        for cls in _wpi_opmode.decorated_opmodes():
            metadata = cls.__dict__.get("_wpilib_opmode_metadata")
            if metadata is None or cls in registered:
                continue
            registered.add(cls)
            try:
                self.add_opmode(
                    cls,
                    metadata.mode,
                    metadata.name,
                    metadata.group,
                    metadata.description,
                    metadata.text_color,
                    metadata.background_color,
                )
            except Exception as e:
                wpilib.report_error(
                    f"Could not register OpMode {cls.__module__}.{cls.__qualname__}: {e}",
                    True,
                )

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

        self._components = components

        self.__opmode_injectables = injectables

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
        assert init_return_type is NoneType, (
            f"{ctyp!r} __init__ had an unexpected non-None return type hint"
        )
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
