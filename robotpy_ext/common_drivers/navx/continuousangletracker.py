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
    
    def nextAngle(self, newAngle):
        adjusted_last_angle = self.last_angle + 360.0 if self.last_angle < 0.0 else self.last_angle
        adjusted_curr_angle = newAngle + 360.0 if newAngle < 0.0 else newAngle
        delta_angle = adjusted_curr_angle - adjusted_last_angle
        self.last_rate = delta_angle

        angle_last_direction = 0
        if adjusted_curr_angle < adjusted_last_angle:
            if delta_angle < -180.0:
                angle_last_direction = -1
            else:
                angle_last_direction = 1
            
        elif adjusted_curr_angle > adjusted_last_angle:
            if delta_angle > 180.0:
                angle_last_direction = -1
            else:
                angle_last_direction = 1
        
        if angle_last_direction < 0:
            if adjusted_curr_angle < 0.0 and adjusted_last_angle >= 0.0:
                self.zero_crossing_count -= 1
                       
        elif angle_last_direction > 0:
            if adjusted_curr_angle >= 0.0 and adjusted_last_angle < 0.0:
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
