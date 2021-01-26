import functools
import inspect
from typing import Callable, Optional

import wpilib

from .magic_tunable import tunable

if wpilib.RobotBase.isSimulation():
    getTime = wpilib.Timer.getFPGATimestamp
else:
    from time import monotonic as getTime


class IllegalCallError(TypeError):
    pass


class NoFirstStateError(ValueError):
    pass


class MultipleFirstStatesError(ValueError):
    pass


class MultipleDefaultStatesError(ValueError):
    pass


class InvalidStateName(ValueError):
    pass


class _State:
    def __init__(
        self,
        f: Callable,
        first: bool = False,
        must_finish: bool = False,
        *,
        duration: Optional[float] = None,
        is_default: bool = False,
    ) -> None:
        name = f.__name__

        # Can't define states that are named the same as things in the
        # base class, will cause issues. Catch it early.
        if hasattr(StateMachine, name):
            raise InvalidStateName(f"cannot have a state named '{name}'")

        # inspect the args, provide a correct call implementation
        allowed_args = "self", "tm", "state_tm", "initial_call"
        sig = inspect.signature(f)
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
                    f"Cannot use keyword-only parameters for function {name}"
                )
            if arg.name in allowed_args:
                args.append(arg.name)
            else:
                invalid_args.append(arg.name)

        if invalid_args:
            raise ValueError(
                "Invalid parameter names in %s: %s" % (name, ",".join(invalid_args))
            )

        self.name = name
        self.description = inspect.getdoc(f)
        self.first = first
        self.must_finish = must_finish
        self.is_default = is_default
        self.duration = duration

        varlist = {"f": f}
        args_code = ",".join(args)
        wrapper_code = f"lambda self, tm, state_tm, initial_call: f({args_code})"
        self.run = eval(wrapper_code, varlist, varlist)

    def __call__(self, *args, **kwargs):
        raise IllegalCallError(
            "Do not call states directly, use begin/next_state instead"
        )

    def __set_name__(self, owner: type, name: str) -> None:
        # Don't allow aliasing of states, it probably won't do what users expect
        if name != self.name:
            raise InvalidStateName(
                f"magicbot state '{self.name}' defined as attribute '{name}'"
            )

        if not issubclass(owner, StateMachine):
            raise TypeError(f"magicbot state {name} defined in non-StateMachine")

        # make durations tunable
        if self.duration is not None:
            duration_attr = name + "_duration"
            # don't create it twice (in case of inheritance overriding)
            if getattr(owner, duration_attr, None) is None:
                setattr(
                    owner,
                    duration_attr,
                    tunable(self.duration, writeDefault=False, subtable="state"),
                )


class _StateData:
    def __init__(self, wrapper):
        self.name = wrapper.name
        self.duration_attr = "%s_duration" % self.name
        self.expires = 0xFFFFFFFF
        self.ran = False
        self.run = wrapper.run
        self.must_finish = wrapper.must_finish

        if hasattr(wrapper, "next_state"):
            self.next_state = wrapper.next_state


def timed_state(
    f: Optional[Callable] = None,
    *,
    duration: float,
    next_state=None,
    first: bool = False,
    must_finish: bool = False,
):
    """
    If this decorator is applied to a function in an object that inherits
    from :class:`.StateMachine`, it indicates that the function
    is a state that will run for a set amount of time unless interrupted.

    It is guaranteed that a timed_state will execute at least once, even if
    it expires prior to being executed.

    The decorated function can have the following arguments in any order:

    - ``tm`` - The number of seconds since the state machine has started
    - ``state_tm`` - The number of seconds since this state has been active
      (note: it may not start at zero!)
    - ``initial_call`` - Set to True when the state is initially called,
      False otherwise. If the state is switched to multiple times, this
      will be set to True at the start of each state execution.

    :param duration: The length of time to run the state before progressing
                     to the next state
    :param next_state: The name of the next state. If not specified, then
                       this will be the last state executed if time expires
    :param first: If True, this state will be ran first
    :param must_finish: If True, then this state will continue executing
                        even if ``engage()`` is not called. However,
                        if ``done()`` is called, execution will stop
                        regardless of whether this is set.
    """

    if f is None:
        return functools.partial(
            timed_state,
            duration=duration,
            next_state=next_state,
            first=first,
            must_finish=must_finish,
        )

    wrapper = _State(f, first, must_finish, duration=duration)

    wrapper.next_state = next_state

    return wrapper


def state(f=None, *, first: bool = False, must_finish: bool = False):
    """
    If this decorator is applied to a function in an object that inherits
    from :class:`.StateMachine`, it indicates that the function
    is a state. The state will continue to be executed until the
    ``next_state`` function is executed.

    The decorated function can have the following arguments in any order:

    - ``tm`` - The number of seconds since the state machine has started
    - ``state_tm`` - The number of seconds since this state has been active
      (note: it may not start at zero!)
    - ``initial_call`` - Set to True when the state is initially called,
      False otherwise. If the state is switched to multiple times, this
      will be set to True at the start of each state execution.

    :param first: If True, this state will be ran first
    :param must_finish: If True, then this state will continue executing
                        even if ``engage()`` is not called. However,
                        if ``done()`` is called, execution will stop
                        regardless of whether this is set.
    """

    if f is None:
        return functools.partial(state, first=first, must_finish=must_finish)

    return _State(f, first, must_finish)


def default_state(f: Callable):
    """
    If this decorator is applied to a method in an object that inherits
    from :class:`.StateMachine`, it indicates that the method
    is a default state; that is, if no other states are executing, this
    state will execute. If the state machine is always executing, the
    default state will never execute.

    There can only be a single default state in a StateMachine object.

    The decorated function can have the following arguments in any order:

    - ``tm`` - The number of seconds since the state machine has started
    - ``state_tm`` - The number of seconds since this state has been active
      (note: it may not start at zero!)
    - ``initial_call`` - Set to True when the state is initially called,
      False otherwise. If the state is switched to multiple times, this
      will be set to True at the start of each state execution.
    """
    return _State(f, first=False, must_finish=True, is_default=True)


def _get_class_members(cls: type) -> dict:
    """Get the members of the given class in definition order, bases first."""
    d = {}
    for cls in reversed(cls.__mro__):
        d.update(cls.__dict__)
    return d


class StateMachine:
    '''
    The StateMachine class is used to implement magicbot components that
    allow one to easily define a `finite state machine (FSM)
    <https://en.wikipedia.org/wiki/Finite-state_machine>`_ that can be
    executed via the magicbot framework.

    You create a component class that inherits from ``StateMachine``.
    Each state is represented as a single function, and you indicate that
    a function is a particular state by decorating it with one of the
    following decorators:

    * :func:`@default_state <.default_state>`
    * :func:`@state <.state>`
    * :func:`@timed_state <.timed_state>`

    As the state machine executes, the decorated function representing the
    current state will be called. Decorated state functions can receive the
    following parameters (all of which are optional):

    - ``tm`` - The number of seconds since autonomous has started
    - ``state_tm`` - The number of seconds since this state has been active
      (note: it may not start at zero!)
    - ``initial_call`` - Set to True when the state is initially called,
      False otherwise. If the state is switched to multiple times, this
      will be set to True at the start of each state.

    To be consistent with the magicbot philosophy, in order for the
    state machine to execute its states you must call the :func:`engage`
    function upon each execution of the main robot control loop. If you do
    not call this function, then execution of the FSM will cease.

    .. note:: If you wish for the FSM to continue executing state functions
              regardless whether ``engage()`` is called, you must set the
              ``must_finish`` parameter in your state decorator to be True.

    When execution ceases (because ``engage()`` was not called), the
    :func:`done` function will be called and the FSM will be reset to the
    starting state. The state functions will not be called again unless
    ``engage`` is called.

    As a magicbot component, StateMachine contains an ``execute`` function that
    will be called on each control loop. All state execution occurs from
    within that function call. If you call other components from a
    StateMachine, you should ensure that your StateMachine is declared
    *before* the other components in your Robot class.

    .. warning:: As StateMachine already contains an execute function,
                 there is no need to define your own ``execute`` function for
                 a state machine component -- if you override ``execute``,
                 then the state machine may not work correctly. Instead,
                 use the :func:`@default_state <.default_state>` decorator.

    Here's a very simple example of how you might implement a shooter
    automation component that moves a ball into a shooter when the
    shooter is ready::

        class ShooterAutomation(magicbot.StateMachine):

            # Some other component
            shooter: Shooter
            ball_pusher: BallPusher

            def fire(self):
                """This is called from the main loop."""
                self.engage()

            @state(first=True)
            def begin_firing(self):
                """
                This function will only be called IFF fire is called and
                the FSM isn't currently in the 'firing' state. If fire
                was not called, this function will not execute.
                """
                self.shooter.enable()
                if self.shooter.ready():
                    self.next_state('firing')

            @timed_state(duration=1.0, must_finish=True)
            def firing(self):
                """
                Because must_finish=True, once the FSM has reached this state,
                this state will continue executing even if engage isn't called.
                """
                self.shooter.enable()
                self.ball_pusher.push()

            #
            # Note that there is no execute function defined as part of
            # this component
            #

        ...

        class MyRobot(magicbot.MagicRobot):
            shooter_automation: ShooterAutomation

            shooter: Shooter
            ball_pusher: BallPusher

            def teleopPeriodic(self):

                if self.joystick.getTrigger():
                    self.shooter_automation.fire()

    This object has a lot of really useful NetworkTables integration as well:

    - tunables are created in /components/NAME/state
      - state durations can be tuned here
      - The 'current state' is output as it happens
      - Descriptions and names of the states are here (for dashboard use)


    .. warning:: This object is not intended to be threadsafe and should not
                 be accessed from multiple threads
    '''

    VERBOSE_LOGGING = False

    #: NT variable that indicates which state will be executed next (though,
    #: does not guarantee that it will be executed). Will return an empty
    #: string if the state machine is not currently engaged.
    current_state = tunable("", subtable="state")

    def __new__(cls):
        # choose to use __new__ instead of __init__
        o = super().__new__(cls)
        o._build_states()
        return o

        # TODO: when this gets invoked, tunables need to be setup on
        # the object first

    def _build_states(self):
        has_first = False

        # problem: the user interface won't know which entries are the
        #          current variables being used by the robot. So, we setup
        #          an array with the names, and the dashboard uses that
        #          to determine the ordering too

        nt_names = []
        nt_desc = []

        states = {}
        cls = type(self)

        default_state = None

        # for each state function:
        for name, state in _get_class_members(cls).items():
            if not isinstance(state, _State):
                continue

            # is this the first state to execute?
            if state.first:
                if has_first:
                    raise MultipleFirstStatesError(
                        "Multiple states were specified as the first state!"
                    )

                self.__first = name
                has_first = True

            state_data = _StateData(state)
            states[name] = state_data
            nt_names.append(name)
            nt_desc.append(state.description or "")

            if state.is_default:
                if default_state is not None:
                    raise MultipleDefaultStatesError(
                        "Multiple default states are not allowed"
                    )
                default_state = state_data

        if not has_first:
            raise NoFirstStateError(
                "Starting state not defined! Use first=True on a state decorator"
            )

        # NOTE: this depends on tunables being bound after this function is called
        cls.state_names = tunable(nt_names, subtable="state")
        cls.state_descriptions = tunable(nt_desc, subtable="state")

        # Indicates that an external party wishes the state machine to execute
        self.__should_engage = False

        # Indicates that the state machine is currently executing
        self.__engaged = False

        # A dictionary of states
        self.__states = states

        # The currently executing state, or None if not executing
        self.__state = None

        # The default state
        self.__default_state = default_state

        # Variable to store time in
        self.__start = 0

    @property
    def is_executing(self):
        """:returns: True if the state machine is executing states"""
        # return self.__state is not None
        return self.__engaged

    def on_enable(self):
        """
        magicbot component API: called when autonomous/teleop is enabled
        """
        pass

    def on_disable(self):
        """
        magicbot component API: called when autonomous/teleop is disabled
        """
        self.done()

    def engage(self, initial_state=None, force=False):
        """
        This signals that you want the state machine to execute its
        states.

        :param initial_state: If specified and execution is not currently
                              occurring, start in this state instead of
                              in the 'first' state
        :param force:         If True, will transition even if the state
                              machine is currently active.
        """
        self.__should_engage = True

        if force or self.__state is None or self.__state is self.__default_state:
            if initial_state:
                self.next_state(initial_state)
            else:
                self.next_state(self.__first)

    def next_state(self, state):
        """Call this function to transition to the next state

        :param state: Name of the state to transition to

        .. note:: This should only be called from one of the state functions
        """
        if isinstance(state, _State):
            state = state.name

        state_data = self.__states[state]
        state_data.ran = False
        self.current_state = state

        self.__state = state_data

    def next_state_now(self, state):
        """Call this function to transition to the next state, and call the next
        state function immediately. Prefer to use :meth:`next_state` instead.

        :param state: Name of the state to transition to

        .. note:: This should only be called from one of the state functions
        """
        self.next_state(state)
        # TODO: may want to do this differently?
        self.execute()

    def done(self):
        """Call this function to end execution of the state machine.

        This function will always be called when a state machine ends. Even if
        the engage function is called repeatedly, done() will be called.

        .. note:: If you wish to do something each time execution ceases,
                  override this function (but be sure to call
                  ``super().done()``!)
        """
        if self.VERBOSE_LOGGING and self.__state is not None:
            self.logger.info("Stopped state machine execution")

        self.__state = None
        self.__engaged = False
        self.current_state = ""

    def execute(self):
        """
        magicbot component API: This is called on each iteration of the
        control loop. Most of the time, you will not want to override
        this function. If you find you want to, you may want to use the
        @default_state mechanism instead.
        """

        now = getTime()

        if not self.__engaged:
            if self.__should_engage:
                self.__start = now
                self.__engaged = True
            elif self.__default_state is None:
                return

        # tm is the number of seconds that the state machine has been executing
        tm = now - self.__start
        state = self.__state
        done_called = False

        # we adjust this so that if we have states chained together,
        # then the total time it runs is the amount of time of the
        # states. Otherwise, the time drifts.
        new_state_start = tm

        # determine if the time has passed to execute the next state
        # -> intentionally comes first
        if state is not None and state.ran and state.expires < tm:
            new_state_start = state.expires

            if state.next_state is None:
                # If the state expires and it's the last state, if the machine
                # is still engaged then it should cycle back to the beginning
                # ... but we should call done() first
                done_called = True
                self.done()

                if self.__should_engage:
                    self.next_state(self.__first)
                    state = self.__state
                else:
                    state = None
            else:
                self.next_state(state.next_state)
                state = self.__state

        # deactivate the current state unless engage was called or
        # must_finish was set
        if not (self.__should_engage or state is not None and state.must_finish):
            state = None

        # if there is no state to execute and there is a default
        # state, do the default state
        if state is None and self.__default_state is not None:
            state = self.__default_state
            if self.__state != state:
                state.ran = False
                self.__state = state

        if state is not None:
            # is this the first time this was executed?
            initial_call = not state.ran
            if initial_call:
                state.ran = True
                state.start_time = new_state_start
                state.expires = new_state_start + getattr(
                    self, state.duration_attr, 0xFFFFFFFF
                )

                if self.VERBOSE_LOGGING:
                    self.logger.info("%.3fs: Entering state: %s", tm, state.name)

            # execute the state function, passing it the arguments
            state.run(self, tm, tm - state.start_time, initial_call)
        elif not done_called:
            # or clear the state
            self.done()

        # Reset this each time
        self.__should_engage = False


class AutonomousStateMachine(StateMachine):
    """
    This is a specialized version of the StateMachine that is designed
    to be used as an autonomous mode. There are a few key differences:

    - The :func:`.engage` function is always called, so the state machine
      will always run to completion unless done() is called
    - VERBOSE_LOGGING is set to True, so a log message will be printed out upon
      each state transition

    """

    VERBOSE_LOGGING = True

    def on_enable(self):
        super().on_enable()
        self.__engaged = True

    def on_iteration(self, tm):
        # TODO, remove the on_iteration function in 2017?

        # Only engage the state machine until its execution finishes, otherwise
        # it will just keep repeating
        #
        # This is because if you keep calling engage(), the state machine will
        # loop. I'm tempted to change that, but I think it would lead to unexpected
        # side effects. Will have to contemplate this...

        if self.__engaged:
            self.engage()
            self.execute()
            self.__engaged = self.is_executing

    def done(self):
        super().done()
        self._StateMachine__should_engage = False
        self.__engaged = False
