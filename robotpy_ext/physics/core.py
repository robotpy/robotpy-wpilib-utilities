'''
    pyfrc supports simplistic custom physics model implementations for
    simulation and testing support. It can be as simple or complex as you want
    to make it. We will continue to add helper functions (such as the 
    :mod:`pyfrc.physics.drivetrains` module) to make this a lot easier
    to do. General purpose physics implementations are welcome also!

    The idea is you provide a :class:`PhysicsEngine` object that overrides specific
    pieces of WPILib, and modifies motors/sensors accordingly depending on the
    state of the simulation. An example of this would be measuring a motor
    moving for a set period of time, and then changing a limit switch to turn 
    on after that period of time. This can help you do more complex simulations
    of your robot code without too much extra effort.

    .. note::

       One limitation to be aware of is that the physics implementation
       currently assumes that you are only calling :func:`wpilib.Timer.delay`
       once per main loop iteration. If you do it more than that, you may get
       some rather funky results.

    By default, pyfrc doesn't modify any of your inputs/outputs without being
    told to do so by your code or the simulation GUI.
    
    See the physics sample for more details.

    Enabling physics support
    ------------------------

    You must create a python module called ``physics.py`` next to your 
    ``robot.py``. A physics module must have a class called
    :class:`PhysicsEngine` which must have a function called ``update_sim``.
    When initialized, it will be passed an instance of this object.
    
    You must also create a 'sim' directory, and place a ``config.json``
    file there, with the following JSON information::
    
        {
          "pyfrc": {
            "robot": {
              "w": 2,
              "h": 3,
              "starting_x": 2,
              "starting_y": 20,
              "starting_angle": 0
            },
            "field": {
              "w": 25,
              "h": 27,
              "px_per_ft": 10
            }
          }
        }
    
'''

import imp
import math
from os.path import exists, join
import threading

import logging
logger = logging.getLogger('pyfrc.physics')

from hal_impl.data import hal_data


def get_engine(robot_path):
    physics_module_path = join(robot_path, 'physics.py')
    if exists(physics_module_path):

        # Load the user's physics module if it exists
        try:
            physics_module = imp.load_source('physics', physics_module_path)
        except:
            logger.exception("Error loading user physics module")
            raise PhysicsInitException()

        if not hasattr(physics_module, 'PhysicsEngine'):
            logger.error("User physics module does not have a PhysicsEngine object")
            raise PhysicsInitException()

        # for now, look for a class called PhysicsEngine
        try:
            engine = physics_module.PhysicsEngine()

            if hasattr(engine, 'initialize'):
                engine.initialize(hal_data)

        except:
            logger.exception("Error creating user's PhysicsEngine object")
            raise PhysicsInitException()

        logger.info("Physics support successfully enabled")

    else:
        logger.warning("Cannot enable physics support, %s not found", physics_module_path)

class PhysicsInitException(Exception):
    pass

class PhysicsEngine:
    '''
        Your physics module must contain a class called ``PhysicsEngine``, 
        and it must implement the same functions as this class.
        
        Alternatively, you can inherit from this object. However, that is
        not required.
    '''

    def __init__(self, hal_data):
        '''
            The constructor may take the following arguments:
            
            :param hal_data: A giant dictionary that has all data about the robot. See
                   ``hal-sim/hal_impl/data.py`` in robotpy-wpilib's repository
                   for more information on the contents of this dictionary.
        '''
        self.state = {}
        
    def initialize(self, hal_data):
        '''
            Called with the hal_data dictionary before the robot has started
            running. Some values may be overwritten when devices are
            initialized... it's not consistent yet, sorry.
        '''
        pass

    def update_sim(self, hal_data, robot_enabled, dt):
        '''
            Called when the simulation parameters for the program need to be
            updated. This is mostly when ``wpilib.Timer.delay()`` is called.
            
            :param hal_data: A giant dictionary that has all data about the robot. See
                             ``hal-sim/hal_impl/data.py`` in robotpy-wpilib's repository
                             for more information on the contents of this dictionary.
            :param robot_enabled: Whether or not the robot is enabled.
            :type  robot_enabled: boolean
            :param dt: The amount of time that has passed since the last
                            time that this function was called
            :type  dt: float
        '''
        pass

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state
