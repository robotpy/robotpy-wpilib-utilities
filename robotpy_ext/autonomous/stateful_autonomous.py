
import wpilib
import networktables

import functools
import inspect

import logging
logger = logging.getLogger('autonomous')


# use this to track ordering of functions, so that we can display them
# properly in the tuning widget on the dashboard
__global_cnt_serial = [0]

def __get_state_serial():
    __global_cnt_serial[0] = __global_cnt_serial[0] + 1
    return __global_cnt_serial[0]

#
# Decorators:
#
#   timed_state 
#
def timed_state(f=None, duration=None, next_state=None, first=False):
    '''
        If this decorator is applied to a function in an object that inherits
        from :class:`.StatefulAutonomous`, it indicates that the function
        is a state.
        
        :param duration: The length of time to run the state before progressing
                         to the next state
        :param next_state: The name of the next state
        :param first: If True, this state will be ran first
    '''
    
    if f is None:
        return functools.partial(timed_state, duration=duration, next_state=next_state, first=first)
    
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    # store state variables here
    wrapper.first = first
    wrapper.name = f.__name__
    wrapper.description = f.__doc__
    wrapper.next_state = next_state
    wrapper.duration = duration
    wrapper.expires = 0xffffffff
    wrapper.ran = False
    wrapper.serial = __get_state_serial()
    
    # inspect the args, provide a correct call implementation
    args, varargs, keywords, defaults = inspect.getargspec(f)
    
    if keywords is not None or varargs is not None:
        raise ValueError("Invalid function parameters for function %s" % wrapper.name)
    
    # TODO: there has to be a better way to do this. oh well.
    
    if len(args) == 1:
        wrapper.run = lambda self, tm, state_tm: f(self)
    elif len(args) == 2:
        if args[1] == 'tm':
            wrapper.run = lambda self, tm, state_tm: f(self, tm)
        elif args[1] == 'state_tm':
            wrapper.run = lambda self, tm, state_tm: f(self, state_tm)
        else:
            raise ValueError("Invalid parameter name for function %s" % wrapper.name)
    elif args == ['self', 'tm', 'state_tm']:
        wrapper.run = lambda self, tm, state_tm: f(self, tm, state_tm)
    elif args == ['self', 'state_tm', 'tm']:
        wrapper.run = lambda self, tm, state_tm: f(self, state_tm, tm)
    else:
        raise ValueError("Invalid parameter names for function %s" % wrapper.name)
    
    
    # provide a default docstring?
    
    return wrapper


        

class StatefulAutonomous:
    '''
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
        
        - ``tm`` - The amount of time that autonomous mode has been running
        - ``state_tm`` - The amount of time that this state has been running
        
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
    '''
    
    __built = False
    __done = False
    
    def __init__(self, components):
        """
            :param components: A dictionary of values that will be assigned
                               as attributes to this object, using the key
                               names in the dictionary
            :type  components: dict
        """
        
        if not hasattr(self, 'MODE_NAME'):
            raise ValueError("Must define MODE_NAME class variable")
        
        for k,v in components.items():
            setattr(self, k, v)
        
        self.__table = networktables.NetworkTable.getTable('SmartDashboard')
        self.__sd_args = []

        self.__build_states()
        self.__tunables = networktables.StringArray()
        
        if hasattr(self, 'initialize'):
            self.initialize()
        
    def register_sd_var(self, name, default, add_prefix=True, vmin=-1, vmax=1):
        '''
            Register a variable that is tunable via NetworkTables/SmartDashboard
            
            When this autonomous mode is enabled, all of the SmartDashboard
            settings will be read and stored as attributes of this object. For
            example, to register a variable 'foo' with a default value of 1::
            
                self.register_sd_var('foo', 1)
                
            This value will show up on NetworkTables as the key ``MODE_NAME\\foo``
            if add_prefix is specified, otherwise as ``foo``.
                
            :param name:     Name of variable to display to user
            :param default:  Default value of variable
            :param add_prefix: Prefix this setting with the mode name
            :type  add_prefix: bool
            :param vmin:     For tuning: minimum value of this variable
            :param vmax:     For tuning: maximum value of this variable
        '''
        
        is_number = self.__register_sd_var_internal(name, default, add_prefix, True)
        
        if not add_prefix:
            return
        
        # communicate the min/max value for numbers to the dashboard
        if is_number:
            name = '%s|%0.3f|%0.3f' % (name, vmin, vmax)
        
        self.__tunables.add(name)
        self.__table.putValue(self.MODE_NAME + '_tunables', self.__tunables)
        
    def __register_sd_var_internal(self, name, default, add_prefix, readback):
        
        is_number = False
        sd_name = name
        
        if add_prefix:
            sd_name = '%s\\%s' % (self.MODE_NAME, name) 
        
        if isinstance(default, bool):
            self.__table.putBoolean(sd_name, default)
            args = (name, sd_name, self.__table.getBoolean)
            
        elif isinstance(default, int) or isinstance(default, float):
            self.__table.putNumber(sd_name, default)
            args = (name, sd_name, self.__table.getNumber)
            is_number = True
            
        elif isinstance(default, str):
            self.__table.putString(sd_name, default)
            args = (name, sd_name, self.__table.getString)
            
        else:
            raise ValueError("Invalid default value")
        
        if readback:
            self.__sd_args.append(args)
        return is_number
    
    def __build_states(self):
    
        has_first = False
    
        states = {}
    
        #for each state function:
        for name in dir(self.__class__):
            
            state = getattr(self.__class__, name)
            if name.startswith('__') or not hasattr(state, 'next_state'):
                continue
            
            # find a pre-execute function if available
            state.pre = getattr(self.__class__, 'pre_%s' % name, None)

            # is this the first state to execute?
            if state.first:
                if has_first:
                    raise ValueError("Multiple states were specified as the first state!")
                
                self.__first = name
                has_first = True
              
            # problem: how do we expire old entries?
            # -> what if we just use json? more flexible, but then we can't tune it
            #    via SmartDashboard
                
            # make the time tunable
            if state.duration is not None:
                self.__register_sd_var_internal(state.name + '_duration', state.duration, True, True)
            
            description = ''
            if state.description is not None:
                description = state.description
            
            states[state.serial] = (state.name, description)
        
        # problem: the user interface won't know which entries are the
        #          current variables being used by the robot. So, we setup
        #          an array with the names, and the dashboard uses that
        #          to determine the ordering too
        
        sorted_states = sorted(states.items())
        
        array = networktables.StringArray()
        
        for _, (name, desc) in sorted_states:
            array.append(name)
            
        self.__table.putValue(self.MODE_NAME + '_durations', array)
        
        array = networktables.StringArray()
        
        for _, (name, desc) in sorted_states:
            array.append(desc)
            
        self.__table.putValue(self.MODE_NAME + '_descriptions', array)
        
        if not has_first:
            raise ValueError("Starting state not defined! Use first=True on a state decorator")
    
        self.__built = True
        
        
        
    def _validate(self):
        # TODO: make sure the state machine can be executed
        # - run at robot time? Probably not. Run this as part of a unit test
        pass
        
    # how long does introspection take? do this in the constructor?
    
    # can do things like add all of the timed states, and project how long
    # it will take to execute it (don't forget about cycles!)
    
    def on_enable(self):
        '''
            Called when autonomous mode is enabled, and initializes the
            state machine internals.
            
            If you override this function, be sure to call it from your
            customized ``on_enable`` function::
            
                super().on_enable()
        '''
        
        if not self.__built:
            raise ValueError('super().__init__(components) was never called!')
        
        # print out the details of this autonomous mode, and any tunables
        
        self.battery_voltage = wpilib.DriverStation.getInstance().getBatteryVoltage()
        logger.info("Battery voltage: %.02fv", self.battery_voltage)
        
        logger.info("Tunable values:")
        
        # read smart dashboard values, print them
        for name, sd_name, fn in self.__sd_args:
            val =  fn(sd_name)
            setattr(self, name, val)
            logger.info("-> %25s: %s" % (name, val))
    
        # set the starting state
        self.next_state(self.__first)
        self.__done = False
    
    def on_disable(self):
        '''Called when the autonomous mode is disabled'''
        pass
    
    
    def next_state(self, name):
        '''Call this function to transition to the next state
        
        :param name: Name of the state to transition to
        '''
        if name is not None:
            self.__state = getattr(self.__class__, name)
        else:
            self.__state = None
            
        if self.__state is None:
            return
        
        self.__state.ran = False
        
    
    def on_iteration(self, tm):
        '''This function is called by the autonomous mode switcher, should
           not be called by enduser code. It is called once per control
           loop iteration.'''
        
        # state: first, name, pre, time
        
        # if you get an error here, then you probably overrode on_enable, 
        # but didn't call super().on_enable()
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
        if not state.ran:
            state.ran = True
            state.start_time = new_state_start
            state.expires = state.start_time + getattr(self, state.name + '_duration')
            
            logger.info("%.3fs: Entering state: %s", tm, state.name)
        
            # execute the pre state if it exists
            if state.pre is not None:
                state.pre(self, tm)
        
        # execute the state
        state.run(self, tm, tm - state.start_time)

    