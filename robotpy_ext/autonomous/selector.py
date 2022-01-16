import importlib
import inspect
import logging
import os
from glob import glob
from typing import Union

import hal
import wpilib

from ..misc.precise_delay import NotifierDelay
from ..misc.simple_watchdog import SimpleWatchdog

logger = logging.getLogger("autonomous")


class AutonomousModeSelector:
    """
    This object loads all modules in a specified python package, and tries
    to automatically discover autonomous modes from them. Each module is
    added to a ``SendableChooser`` object, which allows the user to select
    one of them via SmartDashboard.

    Autonomous mode objects must implement the following functions:

    - ``on_enable`` - Called when autonomous mode is initially enabled
    - ``on_disable`` - Called when autonomous mode is no longer active
    - ``on_iteration`` - Called for each iteration of the autonomous control loop

    Your autonomous object may have the following attributes:

    - ``MODE_NAME`` - The name of the autonomous mode to display to users
    - ``DISABLED`` - If True, don't allow this mode to be selected
    - ``DEFAULT`` - If True, this is the default autonomous mode selected

    Here is an example of using ``AutonomousModeSelector`` in ``TimedRobot``:

    .. code-block:: python

        class MyRobot(wpilib.TimedRobot):

            def robotInit(self):
                self.automodes = AutonomousModeSelector('autonomous')

            def autonomousInit(self):
                self.automodes.start()

            def autonomousPeriodic(self):
                self.automodes.periodic()

            def disabledInit(self):
                self.automodes.disable()

    If you use AutonomousModeSelector, you may also be interested in
    the autonomous state machine helper (:class:`.StatefulAutonomous`).

    Check out the samples in our github repository that show some basic
    usage of ``AutonomousModeSelector``.

    .. note:: If you use AutonomousModeSelector, then you should add
              ``robotpy_ext.autonomous.selector_tests`` to your pyfrc
              unit tests like so::

                  from robotpy_ext.autonomous.selector_tests import *

    .. note::

       For your autonomous mode's ``on_disable`` method to be called,
       you must call :meth:`disable` in ``disabledInit``.

       It is okay to not call :meth:`disable` if you do not need ``on_disable``.
    """

    def __init__(self, autonomous_pkgname, *args, **kwargs):
        """
        :param autonomous_pkgname: Module to load autonomous modes from
        :param args: Args to pass to created autonomous modes
        :param kwargs: Keyword args to pass to created autonomous modes
        """

        self.modes = {}
        self.active_mode = None

        logger.info("Begin initializing autonomous mode switcher")

        # load all modules in specified module
        modules = []

        try:
            autonomous_pkg = importlib.import_module(autonomous_pkgname)
        except ImportError as e:
            if e.name not in [autonomous_pkgname, autonomous_pkgname.split(".")[0]]:
                raise

            # Don't kill the robot because they didn't create an autonomous package
            logger.warning("Cannot load the '%s' package", autonomous_pkgname)
        else:
            if hasattr(autonomous_pkg, "__file__"):
                modules_path = os.path.dirname(os.path.abspath(autonomous_pkg.__file__))
                modules = glob(os.path.join(modules_path, "*.py"))

        for module_filename in modules:

            module = None
            module_name = os.path.basename(module_filename[:-3])

            if module_name in ["__init__"]:
                continue

            try:
                module = importlib.import_module("." + module_name, autonomous_pkgname)
                # module = imp.load_source('.' + module_name, module_filename)
            except:
                if not wpilib.DriverStation.isFMSAttached():
                    raise

            #
            # Find autonomous mode classes in the modules that are present
            # -> note that we actually create the instance of the objects here,
            #    so that way we find out about any errors *before* we get out
            #    on the field..

            for name, obj in inspect.getmembers(module, inspect.isclass):
                mode_name = getattr(obj, "MODE_NAME", None)
                if mode_name is not None:

                    # don't allow the driver to select this mode
                    if getattr(obj, "DISABLED", False):
                        logger.warning(
                            "autonomous mode %s is marked as disabled", obj.MODE_NAME
                        )
                        continue

                    try:
                        instance = obj(*args, **kwargs)
                    except:

                        if not wpilib.DriverStation.isFMSAttached():
                            raise
                        else:
                            continue

                    if mode_name in self.modes:
                        if not wpilib.DriverStation.isFMSAttached():
                            raise RuntimeError(
                                "Duplicate name %s in %s" % (mode_name, module_filename)
                            )

                        logger.error(
                            "Duplicate name %s specified by object type %s in module %s",
                            mode_name,
                            name,
                            module_filename,
                        )
                        self.modes[name + "_" + module_filename] = instance
                    else:
                        self.modes[instance.MODE_NAME] = instance

        # now that we have a bunch of valid autonomous mode objects, let
        # the user select one using the SmartDashboard.

        # SmartDashboard interface
        self.chooser = wpilib.SendableChooser()

        default_modes = []
        mode_names = []

        logger.info("Loaded autonomous modes:")
        for k, v in sorted(self.modes.items()):

            if getattr(v, "DEFAULT", False):
                logger.info(" -> %s [Default]", k)
                self.chooser.setDefaultOption(k, v)
                default_modes.append(k)
            else:
                logger.info(" -> %s", k)
                self.chooser.addOption(k, v)

            mode_names.append(k)

        if len(self.modes) == 0:
            logger.warning("-- no autonomous modes were loaded!")

        self.chooser.addOption("None", None)

        if len(default_modes) == 0:
            self.chooser.setDefaultOption("None", None)
        elif len(default_modes) != 1:
            if not wpilib.DriverStation.isFMSAttached():
                raise RuntimeError(
                    "More than one autonomous mode was specified as default! (modes: %s)"
                    % (", ".join(default_modes))
                )

        # must PutData after setting up objects
        wpilib.SmartDashboard.putData("Autonomous Mode", self.chooser)

        # XXX: Compatibility with the FRC dashboard
        wpilib.SmartDashboard.putStringArray("Auto List", mode_names)

        logger.info("Autonomous switcher initialized")

    def run(
        self,
        control_loop_wait_time=0.020,
        iter_fn=None,
        on_exception=None,
        watchdog: Union[wpilib.Watchdog, SimpleWatchdog] = None,
    ):
        """
        This method implements the entire autonomous loop.

        Do not call this from ``TimedRobot`` as this will break the
        timing of your control loop when your robot switches to teleop.

        This function will NOT exit until autonomous mode has ended. If
        you need to execute code in all autonomous modes, pass a function
        or list of functions as the ``iter_fn`` parameter, and they will be
        called once per autonomous mode iteration.

        :param control_loop_wait_time: Amount of time between iterations
        :param iter_fn: Called at the end of every iteration while
                        autonomous mode is executing
        :param on_exception: Called when an uncaught exception is raised,
                             must take a single keyword arg "forceReport"
        :param watchdog: a WPILib Watchdog to feed every iteration
        """
        if watchdog:
            watchdog.reset()

            if isinstance(watchdog, SimpleWatchdog):
                watchdog_check_expired = watchdog.printIfExpired
            else:

                def watchdog_check_expired():
                    if watchdog.isExpired():
                        watchdog.printEpochs()

        logger.info("Begin autonomous")

        if iter_fn is None:
            iter_fn = (lambda: None,)
        elif not isinstance(iter_fn, (list, tuple)):
            iter_fn = (iter_fn,)

        if on_exception is None:
            on_exception = self._on_exception

        # keep track of how much time has passed in autonomous mode
        timer = wpilib.Timer()
        timer.start()

        try:
            self._on_autonomous_enable()
        except:
            on_exception(forceReport=True)
        if watchdog:
            watchdog.addEpoch("auto on_enable")

        #
        # Autonomous control loop
        #

        observe = hal.observeUserProgramAutonomous
        isAutonomousEnabled = wpilib.DriverStation.isAutonomousEnabled

        with NotifierDelay(control_loop_wait_time) as delay:
            while isAutonomousEnabled():
                observe()
                try:
                    self._on_iteration(timer.get())
                except:
                    on_exception()
                if watchdog:
                    watchdog.addEpoch("auto on_iteration")

                for fn in iter_fn:
                    fn()

                if watchdog:
                    watchdog.addEpoch("robotPeriodic()")
                    watchdog.disable()

                    watchdog_check_expired()

                delay.wait()
                if watchdog:
                    watchdog.reset()

        #
        # Done with autonomous, finish up
        #

        try:
            self.disable()
        except:
            on_exception(forceReport=True)

        logger.info("Autonomous mode ended")

    def start(self) -> None:
        """Start autonomous mode.

        This initialises the selected autonomous mode.
        Call this from your ``autonomousInit`` method.

        .. versionadded:: 2020.1.5
        """
        self.timer = wpilib.Timer()
        self.timer.start()

        self._on_autonomous_enable()

    def periodic(self) -> None:
        """Execute one control loop iteration of the active autonomous mode.

        Call this from your ``autonomousPeriodic`` method.

        .. versionadded:: 2020.1.5
        """
        self._on_iteration(self.timer.get())

    def disable(self) -> None:
        """Disables the active autonomous mode.

        You can call this from your ``disabledInit`` method
        to call your autonomous mode's ``on_disable`` method.

        .. versionadded:: 2020.1.5
        """
        if self.active_mode is not None:
            logger.info("Disabling '%s'", self.active_mode.MODE_NAME)
            self.active_mode.on_disable()

        self.active_mode = None

    #
    #   Internal methods used to implement autonomous mode switching, and
    #   are called automatically
    #

    def _on_autonomous_enable(self):
        """Selects the active autonomous mode and enables it"""

        # XXX: FRC Dashboard compatibility
        # -> if you set it here, you're stuck using it. The FRC Dashboard
        #    doesn't seem to have a default (nor will it show a default),
        #    so the key will only get set if you set it.
        auto_mode = wpilib.SmartDashboard.getString("Auto Selector", None)
        if auto_mode is not None and auto_mode in self.modes:
            logger.info("Using autonomous mode set by LabVIEW dashboard")
            self.active_mode = self.modes[auto_mode]
        else:
            self.active_mode = self.chooser.getSelected()

        if self.active_mode is not None:
            logger.info("Enabling '%s'", self.active_mode.MODE_NAME)
            self.active_mode.on_enable()
        else:
            logger.warning(
                "No autonomous modes were selected, not enabling autonomous mode"
            )

    def _on_iteration(self, time_elapsed):
        """Run the code for the current autonomous mode"""
        if self.active_mode is not None:
            self.active_mode.on_iteration(time_elapsed)

    def _on_exception(self, forceReport=False):
        if not wpilib.DriverStation.isFMSAttached():
            raise
