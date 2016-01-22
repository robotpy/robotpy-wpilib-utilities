#----------------------------------------------------------------------------
# Copyright (c) Kauai Labs 2015. All Rights Reserved.
#
# Created in support of Team 2465 (Kauaibots).  Go Purple Wave!
#
# Open Source Software - may be modified and shared by FRC teams. Any
# modifications to this code must be accompanied by the \License.txt file
# in the root directory of the project
#----------------------------------------------------------------------------

DEFAULT_SPI_BITRATE_HZ = 500000

import hal
from robotpy_ext.misc.crc7 import crc7
from wpilib import SPI, Timer

import logging
logger = logging.getLogger('navx.spi')

class RegisterIO_SPI:
    
    def __init__(self, port, bitrate=None):
        
        if bitrate is None:
            bitrate = DEFAULT_SPI_BITRATE_HZ
        
        simPort = None
        if hal.HALIsSimulation():
            from ._impl.sim_io import NavXSPISim
            simPort = NavXSPISim()
        
        self.port = SPI(port, simPort=simPort)
        self.bitrate = bitrate
        
    def init(self):
        
        logger.info("Initializing NavX SPI")
        
        self.port.setClockRate(self.bitrate)
        self.port.setMSBFirst()
        self.port.setSampleDataOnFalling()
        self.port.setClockActiveLow()
        self.port.setChipSelectActiveLow()
        
        logger.info("Initialized!")
        return True
        
    def write(self, address, value):
        data = [address | 0x80, value]
        data.append(crc7(data))
        if self.port.write(data) != len(data):
            return False
        
        return True
        
    def read(self, first_address, count):
        
        data = [first_address, count]
        data.append(crc7(data))
        retcount = self.port.write(data)
        if retcount != len(data):
            raise IOError("Write error (%s != %s)" % (retcount, len(data)))
        
        Timer.delay(0.001)
        
        data = self.port.read(True, count + 1)
        if len(data) != count + 1:
            raise IOError("Read error (%s != %s)" % (len(data), count+1))
        
        crc = data[-1]
        data = data[:-1]
        
        if crc7(data) != crc:
            raise IOError("CRC error")
        
        return data
    
    def shutdown(self):
        # TODO: should free?
        logger.info("NavX i2c shutdown")
        self.port.free()
        return True
