import functools
import inspect
import logging
from typing import Callable, Optional

import networktables
import wpilib

logger = logging.getLogger("autonomous")


# use this to track ordering of functions, so that we can display them
# properly in the tuning widget on the dashboard
__global_cnt_serial = [0]


def _get_state_serial():
    __global_cnt_serial[0] = __global_cnt_serial[0] + 1
    return __global_cnt_serial[0]


class _State:
    def __init__(self, f: Callable, first: bool):
        # inspect the args, provide a correct call implementation
        allowed_args = "self", "tm", "state_tm", "initial_call"
        sig = inspect.signature(f)
        name = f.__name__

        args = []
        invalid_args = []
        for i, arg in enumerate(sig.parameters.values()):
            if i == 0 and arg.name != "self":
                raise ValueError(f"First argument to {name} must be 'self'")
            if arg.kind is arg.VAR_POSITIONAL:
                raise ValueError(f"Cannot use *args in signature for function {name}")
            if arg.kind is arg.VAR_KEYWORD:
                raise ValueError(
                    f"Cannot use **kwargs in signature for function {name}"
                )
            if arg.kind is arg.KEYWORD_ONLY:
                raise ValueError(
                    "Cannot use keyword-only parameters for function %s" % name
                )
            if arg.name in allowed_args:
                args.append(arg.name)
            else:
                invalid_args.append(arg.name)

        if invalid_args:
            raise ValueError(
                "Invalid parameter names in %s: %s" % (name, ",".join(invalid_args))
            )

        functools.update_wrapper(self, f)

        # store state variables here
        self._func = f
        self.name = name
        self.description = f.__doc__
        self.ran = False
        self.first = first
        self.expires = 0xFFFFFFFF
        self.serial = _get_state_serial()

        varlist = {"f": f}
        args_code = ",".join(args)
        wrapper_code = f"lambda self, tm, state_tm, initial_call: f({args_code})"
        self.run = eval(wrapper_code, varlist, varlist)

    def __call__(self, *args, **kwargs):
        self._func(*args, **kwargs)

    def __set_name__(self, owner: type, name: str) -> None:
        if not issubclass(owner, StatefulAutonomous):
            raise TypeError(
                f"StatefulAutonomous state {name} defined in non-StatefulAutonomous"
            )


#
# Decorators:
#
#   state
#   timed_state
#


def timed_state(
    f: Optional[Callable] = None,
    duration: float = None,
    next_state: str = None,
    first: bool = False,
):
    """
    If this decorator is applied to a function in an object that inherits
    from :class:`.StatefulAutonomous`, it indicates that the function
    is a state that will run for a set amount of time unless interrupted

    The decorated function can have the following arguments in any order:

    - ``tm`` - The number of seconds since autonomous has started
    - ``state_tm`` - The number of seconds since this state has been active
      (note: it may not start at zero!)
    - ``initial_call`` - Set to True when the state is initially called,
      False otherwise. If the state is switched to multiple times, this
      will be set to True at the start of each state.

    :param duration: The length of time to run the state before progressing
                     to the next state
    :param next_state: The name of the next state. If not specified, then
                       this will be the last state executed if time expires
    :param first: If True, this state will be ran first
    """

    if f is None:
        return functools.partial(
            timed_state, duration=duration, next_state=next_state, first=first
        )

    if duration is None:
        raise ValueError("timed_state functions must specify a duration")

    wrapper = _State(f, first)

    wrapper.next_state = next_state
    wrapper.duration = duration

    return wrapper


def state(f: Optional[Callable] = None, first: bool = False):
    """
    If this decorator is applied to a function in an object that inherits
    from :class:`.StatefulAutonomous`, it indicates that the function
    is a state. The state will continue to be executed until the
    ``next_state`` function is executed.

    The decorated function can have the following arguments in any order:

    - ``tm`` - The number of seconds since autonomous has started
    - ``state_tm`` - The number of seconds since this state has been active
      (note: it may not start at zero!)
    - ``initial_call`` - Set to True when the state is initially called,
      False otherwise. If the state is switched to multiple times, this
      will be set to True at the start of each state.

    :param first: If True, this state will be ran first
    """

    if f is None:
        return functools.partial(state, first=first)

    return _State(f, first)


class StatefulAutonomous:
    """
    This object is designed to be used to implement autonomous modes that
    can be used with the :class:`.AutonomousModeSelector` object to select
    an appropriate autonomous mode. However, you don't have to.

    This object is designed to meet the following goals:

    - Supports simple built-in tuning of autonomous mode parameters via
      SmartDashboard
    - Easy to create autonomous modes that support state machine or
      time-based operation
    - Autonomous modes that are easy to read and understand

    You use this by defining a class that inherits from ``StatefulAutonomous``.
    To define each state, you use the :func:`timed_state` decorator on a
    function. When each state is run, the decorated function will be
    called. Decorated functions can receive the following parameters:

    - ``tm`` - The number of seconds since autonomous has started
    - ``state_tm`` - The number of seconds since this state has been active
      (note: it may not start at zero!)
    - ``initial_call`` - Set to True when the state is initially called,
      False otherwise. If the state is switched to multiple times, this
      will be set to True at the start of each state.

    An example autonomous mode that drives the robot forward for 5 seconds
    might look something like this::

        from robotpy_ext.autonomous import StatefulAutonomous

        class DriveForward(StatefulAutonomous):

            MODE_NAME = 'Drive Forward'

            def initialize(self):
                pass

            @timed_state(duration=0.5, next_state='drive_forward', first=True)
            def drive_wait(self):
                pass

            @timed_state(duration=5)
            def drive_forward(self):
                self.drive.move(0, 1, 0)

    Note that in this example, it is assumed that the DriveForward object
    is initialized with a dictionary with a value 'drive' that contains
    an object that has a move function::

        components = {'drive': SomeObject() }
        mode = DriveForward(components)

    If you use this object with :class:`.AutonomousModeSelector`, make sure
    to initialize it with the dictionary, and it will be passed to this
    autonomous mode object when initialized.

    .. seealso:: Check out the samples in our github repository that show
                 some basic usage of ``AutonomousModeSelector``.
    """

    __built = False
    __done = False

    def __init__(self, components=None):
        """
        :param components: A dictionary of values that will be assigned
                           as attributes to this object, using the key
                           names in the dictionary
        :type  components: dict
        """

        if not hasattr(self, "MODE_NAME"):
            raise ValueError("Must define MODE_NAME class variable")

        if components:
            for k, v in components.items():
                setattr(self, k, v)

        self.__table = networktables.NetworkTables.getTable("SmartDashboard")
        self.__sd_args = []

        self.__build_states()
        self.__tunables = []

        if hasattr(self, "initialize"):
            self.initialize()

    def register_sd_var(self, name, default, add_prefix=True, vmin=-1, vmax=1):
        """
        Register a variable that is tunable via NetworkTables/SmartDashboard

        When this autonomous mode is enabled, all of the SmartDashboard
        settings will be read and stored as attributes of this object. For
        example, to register a variable 'foo' with a default value of 1::

            self.register_sd_var('foo', 1)

        This value will show up on NetworkTables as the key ``MODE_NAME\\foo``
        if add_prefix is specified, otherwise as ``foo``.

        :param name:     Name of variable to display to user, cannot have a
                         space in it.
        :param default:  Default value of variable
        :param add_prefix: Prefix this setting with the mode name
        :type  add_prefix: bool
        :param vmin:     For tuning: minimum value of this variable
        :param vmax:     For tuning: maximum value of this variable
        """

        is_number = self.__register_sd_var_internal(name, default, add_prefix, True)

        if not add_prefix:
            return

        # communicate the min/max value for numbers to the dashboard
        if is_number:
            name = "%s|%0.3f|%0.3f" % (name, vmin, vmax)

        self.__tunables.append(name)
        self.__table.putStringArray(self.MODE_NAME + "_tunables", self.__tunables)

    def __register_sd_var_internal(self, name, default, add_prefix, readback):

        if " " in name:
            raise ValueError(
                "ERROR: Cannot use spaces in a tunable variable name (%s)" % name
            )

        is_number = False
        sd_name = name

        if add_prefix:
            sd_name = "%s\\%s" % (self.MODE_NAME, name)

        if isinstance(default, bool):
            self.__table.putBoolean(sd_name, default)
            args = (name, sd_name, self.__table.getBoolean, default)

        elif isinstance(default, int) or isinstance(default, float):
            self.__table.putNumber(sd_name, default)
            args = (name, sd_name, self.__table.getNumber, default)
            is_number = True

        elif isinstance(default, str):
            self.__table.putString(sd_name, default)
            args = (name, sd_name, self.__table.getString, default)

        else:
            raise ValueError("Invalid default value")

        if readback:
            self.__sd_args.append(args)
        return is_number

    def __build_states(self):

        has_first = False

        states = {}
        cls = type(self)

        # for each state function:
        for name in dir(cls):
            state = getattr(cls, name)
            if not isinstance(state, _State):
                continue

            # is this the first state to execute?
            if state.first:
                if has_first:
                    raise ValueError(
                        "Multiple states were specified as the first state!"
                    )

                self.__first = name
                has_first = True

            # problem: how do we expire old entries?
            # -> what if we just use json? more flexible, but then we can't tune it
            #    via SmartDashboard

            # make the time tunable
            if hasattr(state, "duration"):
                self.__register_sd_var_internal(
                    state.name + "_duration", state.duration, True, True
                )

            description = ""
            if state.description is not None:
                description = state.description

            states[state.serial] = (state.name, description)

        # problem: the user interface won't know which entries are the
        #          current variables being used by the robot. So, we setup
        #          an array with the names, and the dashboard uses that
        #          to determine the ordering too

        sorted_states = sorted(states.items())

        self.__table.putStringArray(
            self.MODE_NAME + "_durations", [name for _, (name, desc) in sorted_states]
        )

        self.__table.putStringArray(
            self.MODE_NAME + "_descriptions",
            [desc for _, (name, desc) in sorted_states],
        )

        if not has_first:
            raise ValueError(
                "Starting state not defined! Use first=True on a state decorator"
            )

        self.__built = True

    def _validate(self):
        # TODO: make sure the state machine can be executed
        # - run at robot time? Probably not. Run this as part of a unit test
        pass

    # how long does introspection take? do this in the constructor?

    # can do things like add all of the timed states, and project how long
    # it will take to execute it (don't forget about cycles!)

    def on_enable(self):
        """
        Called when autonomous mode is enabled, and initializes the
        state machine internals.

        If you override this function, be sure to call it from your
        customized ``on_enable`` function::

            super().on_enable()
        """

        if not self.__built:
            raise ValueError("super().__init__(components) was never called!")

        # print out the details of this autonomous mode, and any tunables

        self.battery_voltage = wpilib.DriverStation.getBatteryVoltage()
        logger.info("Battery voltage: %.02fv", self.battery_voltage)

        logger.info("Tunable values:")

        # read smart dashboard values, print them
        for name, sd_name, fn, default in self.__sd_args:
            val = fn(sd_name, default)
            setattr(self, name, val)
            logger.info("-> %25s: %s" % (name, val))

        # set the starting state
        self.next_state(self.__first)
        self.__done = False

    def on_disable(self):
        """Called when the autonomous mode is disabled"""
        pass

    def done(self):
        """Call this function to indicate that no more states should be called"""
        self.next_state(None)

    def next_state(self, name):
        """Call this function to transition to the next state

        :param name: Name of the state to transition to
        """
        if name is not None:
            self.__state = getattr(self.__class__, name)
        else:
            self.__state = None

        if self.__state is None:
            return

        self.__state.ran = False

    def on_iteration(self, tm):
        """This function is called by the autonomous mode switcher, should
        not be called by enduser code. It is called once per control
        loop iteration."""

        # if you get an error here, then you probably overrode on_enable,
        # but didn't call super().on_enable(). Don't do that.
        try:
            state = self.__state
        except AttributeError:
            raise ValueError("super().on_enable was never called!")

        # we adjust this so that if we have states chained together,
        # then the total time it runs is the amount of time of the
        # states. Otherwise, the time drifts.
        new_state_start = tm

        # determine if the time has passed to execute the next state
        if state is not None and state.expires < tm:
            self.next_state(state.next_state)
            new_state_start = state.expires
            state = self.__state

        if state is None:
            if not self.__done:
                logger.info("%.3fs: Done with autonomous mode", tm)
                self.__done = True
            return

        # is this the first time this was executed?
        initial_call = not state.ran
        if initial_call:
            state.ran = True
            state.start_time = new_state_start
            state.expires = state.start_time + getattr(
                self, state.name + "_duration", 0xFFFFFFFF
            )

            logger.info("%.3fs: Entering state: %s", tm, state.name)

        # execute the state function, passing it the arguments
        state.run(self, tm, tm - state.start_time, initial_call)
