
import functools
import inspect
import networktables

from robotpy_ext.misc.orderedclass import OrderedClass

from .magic_tunable import tunable

from wpilib import Timer

class IllegalCallError(Exception):
    pass

class NoFirstStateError(Exception):
    pass

class MultipleFirstStatesError(Exception):
    pass


def _create_wrapper(f, first):
    
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        raise IllegalCallError("Do not call states directly, use begin/next_state instead")
    
    # store state variables here
    wrapper.name = f.__name__
    wrapper.description = f.__doc__
    wrapper.first = first
    
    # inspect the args, provide a correct call implementation
    args, varargs, keywords, _ = inspect.getargspec(f)
    
    if keywords is not None:
        raise ValueError("Cannot use keyword arguments for function %s" % wrapper.name)
    
    if varargs is not None:
        raise ValueError("Cannot use *args arguments for function %s" % wrapper.name)
    
    if args[0] != 'self':
        raise ValueError("First argument must be 'self'")
    
    # TODO: there has to be a better way to do this. oh well. it only runs once.
    
    if len(args) > 4:
        raise ValueError("Too many parameters for %s" % wrapper.name)
    
    wrapper_creator = 'w = lambda self, tm, state_tm, initial_call: f(%s)' % ','.join(args)
    
    for arg in ['self', 'tm', 'state_tm', 'initial_call']:
        try:
            args.remove(arg)
        except ValueError:
            pass
    
    if len(args) != 0:
        raise ValueError("Invalid parameter names in %s: %s" % (wrapper.name, ','.join(args)))
    
    varlist = {'f': f}
    exec(wrapper_creator, varlist, varlist)
    
    wrapper.run = varlist['w']    
    return wrapper

class _StateData:
    def __init__(self, wrapper):
        self.name = wrapper.name
        self.duration_attr = '%s_duration' % self.name
        self.expires = 0xffffffff
        self.ran = False
        self.run = wrapper.run
        
        if hasattr(wrapper, 'next_state'):
            self.next_state = wrapper.next_state

def timed_state(f=None, *, duration=None, next_state=None, first=False):
    '''
        If this decorator is applied to a function in an object that inherits
        from :class:`.StateMachine`, it indicates that the function
        is a state that will run for a set amount of time unless interrupted
        
        The decorated function can have the following arguments in any order:
        
        - ``tm`` - The number of seconds since the state machine has started
        - ``state_tm`` - The number of seconds since this state has been active
          (note: it may not start at zero!)
        - ``initial_call`` - Set to True when the state is initially called,
          False otherwise. If the state is switched to multiple times, this
          will be set to True at the start of each state.
        
        :param duration: The length of time to run the state before progressing
                         to the next state
        :type  duration: float
        :param next_state: The name of the next state. If not specified, then
                           this will be the last state executed if time expires
        :type  next_state: str
        :param first: If True, this state will be ran first
        :type  first: bool
    '''
    
    if f is None:
        return functools.partial(timed_state, duration=duration, next_state=next_state, first=first)
    
    if duration is None:
        raise ValueError("timed_state functions must specify a duration")
    
    wrapper = _create_wrapper(f, first)
    
    wrapper.next_state = next_state
    wrapper.duration = duration
    
    return wrapper

def state(f=None, *, first=False):
    '''
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
          will be set to True at the start of each state.
        
        :param first: If True, this state will be ran first
        :type  first: bool
    '''
    
    if f is None:
        return functools.partial(state, first=first)
    
    return _create_wrapper(f, first)



class StateMachine(metaclass=OrderedClass):
    '''
        This object is designed to be used to easily implement magicbot
        components that are basically a big state machine.
        
        You use this by defining a class that inherits from ``StateMachine``.
        To define each state, you use the :func:`timed_state` decorator on a
        function. When each state is run, the decorated function will be
        called. Decorated functions can receive the following parameters:
        
        - ``tm`` - The number of seconds since autonomous has started
        - ``state_tm`` - The number of seconds since this state has been active
          (note: it may not start at zero!)
        - ``initial_call`` - Set to True when the state is initially called,
          False otherwise. If the state is switched to multiple times, this
          will be set to True at the start of each state.
        
        As a magicbot component, this contains an ``execute`` function that
        will be called on each control loop. If you call other components from
        this component, you should ensure that your component occurs *before*
        the other components in your Robot class.
        
        Here's a very simple example of how you might implement a shooter
        automation component that moves a ball into a shooter when the
        shooter is ready::
        
            class ShooterAutomation:
            
                # Some other component
                shooter = Shooter
                ball_pusher = BallPusher
                
                
                def fire(self):
                    """This is called from the main loop"""
                    self.begin()
                    
                @state(first=True)
                def begin_firing(self):
                    self.shooter.enable()
                    if self.shooter.ready():
                        self.next_state('firing')
                    
                @timed_state(duration=1.0)
                def firing(self):
                    self.shooter.enable()
                    self.ball_pusher.push()
            
            ...
                
            class MyRobot(magicbot.MagicRobot):
            
                ...
                
                def teleopPeriodic(self):
                
                    if self.joystick.getTrigger():
                        self.shooter_automation.fire()
                        
        This object has a lot of really useful NetworkTables integration
        as well:
        
        - tunables are created in /components/NAME/state
          - state durations can be tuned here
          - The 'current state' is output as it happens
          - Descriptions and names of the states are here (for dashboard use)
        
    '''
    
    VERBOSE_LOGGING = False
    
    current_state = tunable('', subtable='state')
    
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
        
        nt_names = networktables.StringArray()
        nt_desc = networktables.StringArray()
    
        states = {}
        cls = self.__class__
    
        #for each state function:
        for name in self.members:
            
            state = getattr(cls, name)
            if name.startswith('__') or not hasattr(state, 'first'):
                continue

            # is this the first state to execute?
            if state.first:
                if has_first:
                    raise MultipleFirstStatesError("Multiple states were specified as the first state!")
                
                self.__first = name
                has_first = True
            
            description = ''
            if state.description is not None:
                description = state.description
            
            state_data = _StateData(state)
            states[state.name] = state_data
            nt_names.append(state.name)
            nt_desc.append(description)
            
            # make the time tunable
            # -> this depends on tunables being bound after this function is called
            if hasattr(state, 'duration'):
                # don't create it twice (in case of mutliple instances)
                prop = getattr(cls, state_data.duration_attr, None)
                if prop is None:
                    prop = setattr(cls, state_data.duration_attr, tunable(state.duration, writeDefault=False, subtable='state'))
        
        cls.state_names = tunable(nt_names, subtable='state')
        cls.state_descriptions = tunable(nt_desc, subtable='state')
         
        if not has_first:
            raise NoFirstStateError("Starting state not defined! Use first=True on a state decorator")
        
        self.__executing = False
        self.__states = states
        self.__state = None
        
    @property
    def is_executing(self):
        ''':returns: True if the state machine is executing states'''
        return self.__state is not None
        
    def on_enable(self):
        '''
            magicbot component API: called when autonomous/teleop is enabled
        '''
        pass
    
    def on_disable(self):
        '''
            magicbot component API: called when autonomous/teleop is disabled
        '''
        self.done()
    
    def begin(self, initial_state=None, force=False):
        '''
            Call this to begin execution of the state machine
        
            :param initial_state: If specified, start in this state instead
                                  of in the 'first' state
            :param force:         If True, will transition even if the state
                                  machine is currently active.
        '''
        if force or not self.__executing:
            self.__start = Timer.getFPGATimestamp()
            if initial_state:
                self.next_state(initial_state)
            else:
                self.next_state(self.__first)
    
    def next_state(self, name):
        '''Call this function to transition to the next state
        
        :param name: Name of the state to transition to
        
        .. note:: This should only be called from one of the state functions
        '''
        if name is not None:
            self.__state = self.__states[name]
        else:
            self.__state = None
            
        if self.__state is None:
            self.__executing = False
            self.current_state = ''
            return
        
        self.__executing = True
        self.current_state = self.__state.name
        self.__state.ran = False
        
    def next_state_now(self, name):
        '''Call this function to transition to the next state, and call the next
        state function immediately. Prefer to use :meth:`next_state` instead.
        
        :param name: Name of the state to transition to
        '''
        self.next_state(name)
        self.execute()
        
    def done(self):
        '''Call this function to indicate that no more states should be called'''
        self.next_state(None)
    
    def execute(self):
        '''
            magicbot component API: This is called on each iteration of the
            control loop. Most of the time, you will not want to override
            this function.
        '''
        
        if not self.__executing:
            return
        
        now = Timer.getFPGATimestamp()
        tm = now - self.__start
        
        # if you get an error here, then _build_states was never called
        try:
            state = self.__state
        except AttributeError:
            raise ValueError("_build_states was never called!")
        
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
            if self.__executing:
                if self.VERBOSE_LOGGING:
                    self.logger.info("%.3fs: End of state machine", tm)
                self.__executing = False
            return
        
        # is this the first time this was executed?
        initial_call = not state.ran
        if initial_call:
            state.ran = True
            state.start_time = new_state_start
            state.expires = new_state_start + getattr(self, state.duration_attr, 0xffffffff)
            
            if self.VERBOSE_LOGGING:
                self.logger.info("%.3fs: Entering state: %s", tm, state.name)
        
        # execute the state function, passing it the arguments
        state.run(self, tm, tm - state.start_time, initial_call)

    
class AutonomousStateMachine(StateMachine):
    '''
        This is a specialized version of the StateMachine that is designed
        to be used as an autonomous mode.
    '''
    
    VERBOSE_LOGGING = True
    
    def on_enable(self):
        self.begin()
            
    def on_disable(self):
        # maybe this should always happen?
        self.done()
        
    def on_iteration(self, tm):
        # TODO, remove this in 2017
        self.execute()   
