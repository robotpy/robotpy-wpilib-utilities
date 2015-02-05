
from glob import glob
import importlib
import inspect
import os

import logging
logger = logging.getLogger('autonomous')

from ..misc.precise_delay import PreciseDelay

import wpilib


class AutonomousModeSelector:
    '''
        This object loads all modules in a specified python package, and tries
        to automatically discover autonomous modes from them. Each module is 
        added to a ``SendableChooser`` object, which allows the user to select
        one of them via the SmartDashboard/SFX.
        
        Autonomous mode objects must implement the following functions:
        
        - ``on_enable`` - Called when autonomous mode is initially enabled
        - ``on_disable`` - Called when autonomous mode is no longer active
        - ``on_iteration`` - Called for each iteration of the autonomous control loop
        
        Your autonomous object may have the following attributes:
        
        - ``MODE_NAME`` - The name of the autonomous mode to display to users
        - ``DISABLED`` - If True, don't allow this mode to be selected
        - ``DEFAULT`` - If True, this is the default autonomous mode selected
        
        AutonomousModeSelector can be easily used from either ``IterativeRobot``
        or from ``SampleRobot``. For ``IterativeRobot``, the simplest usage would
        look like so::
        
            class MyRobot(wpilib.IterativeRobot):
            
                def robotInit(self):
                    self.automodes = AutonomousModeSelector()
            
                def autonomousPeriodic(self):
                    self.automodes.run()
                    
        
        For ``SampleRobot``, for the simplest usage you would do this::
        
            class MyRobot(wpilib.SampleRobot):
            
                def robotInit(self):
                    self.automodes = AutonomousModeSelector()
            
                def autonomous(self):
                    self.automodes.run()
       
        If you use AutonomousModeSelector, you may also be interested in
        the autonomous state machine helper (:class:`.StatefulAutonomous`).
        
        .. note:: If you use AutonomousModeSelector, then you should add
                  ``robotpy_ext.autonomous.selector_tests`` to your pyfrc
                  unit tests like so::
                  
                      from robotpy_ext.autonomous.selector_tests import *
    '''
    
    def __init__(self, autonomous_pkgname, *args, **kwargs):
        '''
            :param autonomous_pkgname: Module to load autonomous modes from
            :param args: Args to pass to created autonomous modes
            :param kwargs: Keyword args to pass to created autonomous modes
        '''
        
        self.ds = wpilib.DriverStation.getInstance()
        self.modes = {}
        self.active_mode = None
        
        logger.info("Begin initializing autonomous mode switcher")
        
        # load all modules in specified module
        autonomous_pkg = importlib.import_module(autonomous_pkgname) 
        
        modules_path = os.path.dirname(os.path.abspath(autonomous_pkg.__file__))
        modules = glob(os.path.join(modules_path, '*.py' ))
        
        for module_filename in modules:
            
            module_name = os.path.basename(module_filename[:-3])
            
            if module_name in  ['__init__', 'manager']:
                continue
        
            try:
                module = importlib.import_module('.' + module_name, autonomous_pkgname)
                #module = imp.load_source('.' + module_name, module_filename)
            except:
                if not self.ds.isFMSAttached():
                    raise
            
            #
            # Find autonomous mode classes in the modules that are present
            # -> note that we actually create the instance of the objects here,
            #    so that way we find out about any errors *before* we get out 
            #    on the field.. 
            
            for name, obj in inspect.getmembers(module, inspect.isclass):

                if hasattr(obj, 'MODE_NAME') :
                    
                    # don't allow the driver to select this mode 
                    if hasattr(obj, 'DISABLED') and obj.DISABLED:
                        logger.warn("autonomous mode %s is marked as disabled", obj.MODE_NAME)
                        continue
                    
                    try:
                        instance = obj(*args, **kwargs)
                    except:
                        
                        if not self.ds.isFMSAttached():
                            raise
                        else:
                            continue
                    
                    if instance.MODE_NAME in self.modes:
                        if not self.ds.isFMSAttached():
                            raise RuntimeError( "Duplicate name %s in %s" % (instance.MODE_NAME, module_filename) )
                        
                        logger.error("Duplicate name %s specified by object type %s in module %s", instance.MODE_NAME, name, module_filename)
                        self.modes[name + '_' + module_filename] = instance
                    else:
                        self.modes[instance.MODE_NAME] = instance
        
        # now that we have a bunch of valid autonomous mode objects, let 
        # the user select one using the SmartDashboard.
        
        # SmartDashboard interface
        self.chooser = wpilib.SendableChooser()
        
        default_modes = []
        
        logger.info("Loaded autonomous modes:")
        for k,v in sorted(self.modes.items()):
            
            if hasattr(v, 'DEFAULT') and v.DEFAULT == True:
                logger.info(" -> %s [Default]", k)
                self.chooser.addDefault(k, v)
                default_modes.append(k)
            else:
                logger.info( " -> %s", k )
                self.chooser.addObject(k, v)
        
        if len(self.modes) == 0:
            logger.warn("-- no autonomous modes were loaded!")
                
        self.chooser.addObject('None', None)
        
        if len(default_modes) == 0:
            self.chooser.addDefault('None', None)
        elif len(default_modes) != 1:
            if not self.ds.isFMSAttached():
                raise RuntimeError("More than one autonomous mode was specified as default! (modes: %s)" % (', '.join(default_modes)))
            
                
        # must PutData after setting up objects
        wpilib.SmartDashboard.putData('Autonomous Mode', self.chooser)
        
        logger.info("Autonomous switcher initialized")
    
            
    def run(self, control_loop_wait_time=0.020, iter_fn=None):    
        '''
            This function does everything required to implement autonomous
            mode behavior. You should call this from your autonomous mode
            function -- ``autonomousPeriodic`` in :class:`.IterativeRobot`,
            or ``autonomous`` in :class:`.SampleRobot`.
            
            This function will NOT exit until autonomous mode has ended. If
            you need to execute code in all autonomous modes, pass a function
            as the ``iter_fn`` parameter, and it will be called once per
            autonomous mode iteration.
                          
            :param control_loop_wait_time: Amount of time between iterations
            :param iter_fn: Called at the end of every iteration while
                            autonomous mode is executing
        '''
        
        logger.info("Begin autonomous")
        
        if iter_fn is None:
            iter_fn = lambda: None
        
        # keep track of how much time has passed in autonomous mode
        timer = wpilib.Timer()
        timer.start()
        
        try:
            self._on_autonomous_enable()
        except:
            if not self.ds.isFMSAttached():
                raise
        
        #
        # Autonomous control loop
        #
        
        delay = PreciseDelay(control_loop_wait_time)
        
        while self.ds.isAutonomous() and self.ds.isEnabled():
 
            try:            
                self._on_iteration(timer.get())
            except:
                if not self.ds.isFMSAttached():
                    raise
            
            iter_fn()
             
            delay.wait()
            
        #
        # Done with autonomous, finish up
        #
            
        try:
            self._on_autonomous_disable()
        except:
            if not self.ds.isFMSAttached():
                raise
            
        logger.info("Autonomous mode ended")
        
    #
    #   Internal methods used to implement autonomous mode switching, and
    #   are called automatically
    #
    
    def _on_autonomous_enable(self):
        '''Selects the active autonomous mode and enables it'''
        self.active_mode = self.chooser.getSelected()
        if self.active_mode is not None:
            logger.info("Enabling '%s'" % self.active_mode.MODE_NAME)
            self.active_mode.on_enable()
        else:
            logger.warn("No autonomous modes were selected, not enabling autonomous mode")
 
    def _on_autonomous_disable(self):
        '''Disable the active autonomous mode'''
        if self.active_mode is not None:
            logger.info("Disabling '%s'" % self.active_mode.MODE_NAME)
            self.active_mode.on_disable()
            
        self.active_mode = None
        
    def _on_iteration(self, time_elapsed):
        '''Run the code for the current autonomous mode'''
        if self.active_mode is not None:
            self.active_mode.on_iteration(time_elapsed)

