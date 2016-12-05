#!/usr/bin/env python3

import wpilib

from robotpy_ext.autonomous import AutonomousModeSelector

class MyRobot(wpilib.IterativeRobot):
    
    def robotInit(self):
        
        # Simple two wheel drive
        self.drive = wpilib.RobotDrive(0, 1)
        self.drive.setSafetyEnabled(False)
        
        # Items in this dictionary are available in your autonomous mode
        # as attributes on your autonomous object
        self.components = {
            'drive': self.drive
        }
        
        # * The first argument is the name of the package that your autonomous
        #   modes are located in
        # * The second argument is passed to each StatefulAutonomous when they
        #   start up
        self.automodes = AutonomousModeSelector('autonomous',
                                                self.components)
    
    def autonomousPeriodic(self):
        self.automodes.run()
    
    def teleopInit(self):
        pass
    
    def teleopPeriodic(self):
        pass
    
if __name__ == '__main__':
    wpilib.run(MyRobot)