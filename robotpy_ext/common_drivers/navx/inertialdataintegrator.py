#----------------------------------------------------------------------------
# Copyright (c) Kauai Labs 2015. All Rights Reserved.
#
# Created in support of Team 2465 (Kauaibots).  Go Purple Wave!
#
# Open Source Software - may be modified and shared by FRC teams. Any
# modifications to this code must be accompanied by the \License.txt file
# in the root directory of the project
#----------------------------------------------------------------------------


class InertialDataIntegrator:
    
    def __init__(self):
        self.resetDisplacement()
    
    def updateDisplacement(self, accel_x_g, accel_y_g,
                           update_rate_hz, is_moving):
        if is_moving:
            accel_g = (accel_x_g, accel_y_g)
            sample_time = 1.0 / update_rate_hz
            
            for i in range(2):
                m_s2 = accel_g[i] * 9.80665
                self.displacement[i] += self.last_velocity[i] + (0.5 * m_s2 * sample_time * sample_time)
                self.last_velocity[i] = self.last_velocity[i] + (m_s2 * sample_time)
        else:
            self.last_velocity[0] = 0
            self.last_velocity[1] = 0
            
    def resetDisplacement(self):
        self.displacement = [0, 0]
        self.last_velocity = [0, 0]
    
    def getVelocityX(self):
        return self.last_velocity[0]
    
    def getVelocityY(self):
        return self.last_velocity[1]
    
    def getVelocityZ(self):
        return 0
    
    def getDisplacementX(self):
        return self.displacement[0]
    
    def getDisplacementY(self):
        return self.displacement[1]
    
    def getDisplacementZ(self):
        return 0
