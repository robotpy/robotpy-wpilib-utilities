# validated: 2017-02-19 DS c5e3a8a9b642 roborio/java/navx_frc/src/com/kauailabs/navx/frc/ContinuousAngleTracker.java
#----------------------------------------------------------------------------
# Copyright (c) Kauai Labs 2015. All Rights Reserved.
#
# Created in support of Team 2465 (Kauaibots).  Go Purple Wave!
#
# Open Source Software - may be modified and shared by FRC teams. Any
# modifications to this code must be accompanied by the \License.txt file
# in the root directory of the project
#----------------------------------------------------------------------------

import threading

class ContinuousAngleTracker:
    
    def __init__(self):
        self._init()
        self.angleAdjust = 0.0
        self.lock = threading.Lock()
        
    def _init(self):
        self.gyro_prevVal = 0.0
        self.ctrRollOver  = 0
        self.fFirstUse = True
        self.last_yaw_angle = 0.0
        self.curr_yaw_angle = 0.0
    
    def nextAngle(self, newAngle):
        
        with self.lock:
            self.last_yaw_angle = self.curr_yaw_angle
            self.curr_yaw_angle = newAngle
    
    def reset(self):
        '''Invoked (internally) whenever yaw reset occurs.'''
        with self.lock:
            self._init()
    
    def getAngle(self):
        # First case
        # Old reading: +150 degrees
        # New reading: +170 degrees
        # Difference:  (170 - 150) = +20 degrees
        
        # Second case
        # Old reading: -20 degrees
        # New reading: -50 degrees
        # Difference : (-50 - -20) = -30 degrees 
        
        # Third case
        # Old reading: +179 degrees
        # New reading: -179 degrees
        # Difference:  (-179 - 179) = -358 degrees
        
        # Fourth case
        # Old reading: -179  degrees
        # New reading: +179 degrees
        # Difference:  (+179 - -179) = +358 degrees
        
        with self.lock:
            yawVal = self.curr_yaw_angle
            
            # Has gyro_prevVal been previously set?
            # If not, return do not calculate, return current value
            if not self.fFirstUse:
                
                # Determine count for rollover counter
                difference = yawVal - self.gyro_prevVal

                # Clockwise past +180 degrees
                # If difference > 180*, increment rollover counter
                if difference < -180.0:
                    self.ctrRollOver += 1

                # Counter-clockwise past -180 degrees:
                # If difference > 180*, decrement rollover counter
                
                elif difference > 180.0:
                    self.ctrRollOver -= 1
            
            # Mark gyro_prevVal as being used
            self.fFirstUse = False
                
            # Calculate value to return back to calling function
            # e.g. +720 degrees or -360 degrees
            gyroVal = yawVal + (360.0 * self.ctrRollOver)
            self.gyro_prevVal = yawVal
            
            return gyroVal + self.angleAdjust

    def setAngleAdjustment(self, adjustment):
        self.angleAdjust = adjustment
        
    def getAngleAdjustment(self):
        return self.angleAdjust
    
    def getRate(self):
        with self.lock:
            difference = self.curr_yaw_angle - self.last_yaw_angle
            
        if difference > 180.0:
            # Clockwise past +180 degrees
            difference = 360.0 - difference
        elif difference < -180.0:
            # Counter-clockwise past -180 degrees
            difference = 360.0 + difference
        
        return difference

