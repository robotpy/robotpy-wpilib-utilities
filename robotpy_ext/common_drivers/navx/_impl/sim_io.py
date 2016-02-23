
from . import AHRSProtocol
from . import IMURegisters

from hal_impl.data import hal_data

from hal_impl.i2c_helpers import I2CSimBase
from hal_impl.spi_helpers import SPISimBase

from ....misc.crc7 import crc7

class NavXSimBase:
    """
        This is a really quick hack to get the NavX working in simulation.
        
        If you wish to do more advanced things with this, please add the
        features and make a pull request. :)
    """
    
    def __init__(self):
        self.cap_flags = AHRSProtocol.NAVX_CAPABILITY_FLAG_YAW_RESET
    
    def _write(self, data):
        
        reg = data[0] & 0x7F
        
        if reg == IMURegisters.NAVX_REG_INTEGRATION_CTL:
            if data[0] == AHRSProtocol.NAVX_INTEGRATION_CTL_RESET_YAW:
                hal_data['robot'][self.angle_key] = 0
                
    
    def _read(self, data, count):
        # We only really support two calls, so cheat here
        
        # config buffer
        if count == 18:
            data[IMURegisters.NAVX_REG_WHOAMI] = IMURegisters.NAVX_MODEL_NAVX_MXP
            AHRSProtocol.encodeBinaryUint16(self.cap_flags, data, IMURegisters.NAVX_REG_CAPABILITY_FLAGS_L)
        
        # data
        elif count == 82:
            
            AHRSProtocol.encodeBinaryUint16(self.cap_flags, data, IMURegisters.NAVX_REG_CAPABILITY_FLAGS_L)
            
            # NavX returns angle in 180 to -180, angle key is continuous
            
            angle = hal_data['robot'].get(self.angle_key, 0)
            angle = ((angle + 180) % 360.0) - 180.0
            AHRSProtocol.encodeProtocolSignedHundredthsFloat(angle, data, IMURegisters.NAVX_REG_YAW_L-4)
            
        # no idea
        else:
            raise NotImplementedError("Oops")
        
class NavXI2CSim(NavXSimBase, I2CSimBase):
    
    def i2CInitialize(self, port, status):
        status.value = 0
        
        # TODO: support other sim parameters
        self.angle_key = 'navxmxp_i2c_%d_angle' % port
        
    def i2CWrite(self, port, device_address, data_to_send, send_size):
        self._write(data_to_send)
        return send_size
    
    def i2CRead(self, port, device_address, buffer, count):
        self._read(buffer, count)
        return count

class NavXSPISim(NavXSimBase, SPISimBase):
    
    def spiInitialize(self, port, status):
        status.value = 0
        
        # TODO: support other sim parameters
        self.angle_key = 'navxmxp_spi_%d_angle' % port
    
    def spiWrite(self, port, data_to_send, send_size):
        self._write(data_to_send)
        return send_size
    
    def spiTransaction(self, port, data_to_send, data_received, size):
        self._read(data_received, size - 1)
        # TODO: maybe disable crc in sim
        data_received[-1] = crc7(data_received[:-1])
        return size

