#----------------------------------------------------------------------------
# Copyright (c) Kauai Labs 2015. All Rights Reserved.
#
# Created in support of Team 2465 (Kauaibots).  Go Purple Wave!
#
# Open Source Software - may be modified and shared by FRC teams. Any
# modifications to this code must be accompanied by the \License.txt file
# in the root directory of the project
#----------------------------------------------------------------------------

import hal
import wpilib

import logging
logger = logging.getLogger('navx.i2c')

MAX_WPILIB_I2C_READ_BYTES = 127

class RegisterIO_I2C:
    
    def __init__(self, port):
        
        simPort = None
        if hal.HALIsSimulation():
            from ._impl.sim_io import NavXI2CSim
            simPort = NavXI2CSim()
        
        self.port = wpilib.I2C(port, 0x32, simPort=simPort)
        
    def init(self):
        logger.info("NavX i2c initialized")
        return True
    
    def write(self, address, value):
        return self.port.write(address | 0x80, value)
    
    def read(self, first_address, count):
        buffer = []
        l = 0
        while l != count:
            read_len = min(MAX_WPILIB_I2C_READ_BYTES, count - l)
            if not self.port.write(first_address + l, read_len):
                data = self.port.readOnly(read_len)
                if not data:
                    break
                
                buffer.extend(data)
                l = len(buffer)
            else:
                break
        
        if l != count:
            raise IOError("Read error")
        
        return buffer
    
    def shutdown(self):
        logger.info("NavX i2c shutdown")
        self.port.free()
        return True
