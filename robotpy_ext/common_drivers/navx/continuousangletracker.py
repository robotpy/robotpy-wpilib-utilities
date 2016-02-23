#----------------------------------------------------------------------------
# Copyright (c) Kauai Labs 2015. All Rights Reserved.
#
# Created in support of Team 2465 (Kauaibots).  Go Purple Wave!
#
# Open Source Software - may be modified and shared by FRC teams. Any
# modifications to this code must be accompanied by the \License.txt file
# in the root directory of the project
#----------------------------------------------------------------------------

class ContinuousAngleTracker:
    
    def __init__(self):
        self.last_angle = 0.0
        self.zero_crossing_count = 0
        self.last_rate = 0
        self.first_sample = True
    
    def nextAngle(self, newAngle):
        
        # If the first received sample is negative, 
        # ensure that the zero crossing count is
        # decremented.
        
        if self.first_sample:
            self.first_sample = False
            if newAngle < 0.0:
                self.zero_crossing_count -= 1
        
        # Calculate delta angle, adjusting appropriately
        # if the current sample crossed the -180/180
        # point.
        
        
        bottom_crossing = False
        delta_angle = newAngle - self.last_angle
        
        # Adjust for wraparound at -180/+180 point
        if delta_angle >= 180.0:
            delta_angle = 360.0 - delta_angle
            bottom_crossing = True
        elif delta_angle <= -180.0:
            delta_angle = 360.0 + delta_angle;
            bottom_crossing = True
        
        self.last_rate = delta_angle

        # If a zero crossing occurred, increment/decrement
        # the zero crossing count appropriately.
        if not bottom_crossing:
            if delta_angle < 0.0:
                if (newAngle < 0.0) and (self.last_angle >= 0.0):
                    self.zero_crossing_count -= 1
            elif delta_angle >= 0.0:
                if (newAngle >= 0.0) and (self.last_angle < 0.0):
                    self.zero_crossing_count += 1
        
        self.last_angle = newAngle
    
    def getAngle(self):
        accumulated_angle = self.zero_crossing_count * 360.0
        curr_angle = self.last_angle
        if curr_angle < 0.0:
            curr_angle += 360.0
        
        accumulated_angle += curr_angle
        return accumulated_angle
    
    def getRate(self):
        return self.last_rate
