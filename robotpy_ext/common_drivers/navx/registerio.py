# validated: 2017-02-19 DS c5e3a8a9b642 roborio/java/navx_frc/src/com/kauailabs/navx/frc/RegisterIO.java
#----------------------------------------------------------------------------
# Copyright (c) Kauai Labs 2015. All Rights Reserved.
#
# Created in support of Team 2465 (Kauaibots).  Go Purple Wave!
#
# Open Source Software - may be modified and shared by FRC teams. Any
# modifications to this code must be accompanied by the \License.txt file
# in the root directory of the project
#----------------------------------------------------------------------------

from ._impl import AHRSProtocol, IMUProtocol, IMURegisters

from wpilib.timer import Timer

import logging
logger = logging.getLogger('navx')

__all__ = ['RegisterIO']

IO_TIMEOUT_SECONDS = 1.0
DELAY_OVERHEAD_SECONDS = 0.004


class _BoardId:
    type = 0
    hw_rev = 0
    fw_ver_major = 0
    fw_ver_minor = 0
    fw_revision = 0
    unique_id = [0]*12

class _BoardState:
    op_status = 0
    sensor_status = 0
    cal_status = 0
    selftest_status = 0
    capability_flags = 0
    update_rate_hz = 0
    accel_fsr_g = 0
    gyro_fsr_dps = 0

class RegisterIO:
    
    def __init__(self, io_provider, update_rate_hz, notify_sink, board_capabilities):
        """
            :param board_capabilities: must have the following callable attributes:
                _isOmniMountSupported, _isBoardYawResetSupported,
                _isDisplacementSupported
        
            :param notify_sink: must have the following callable attributes: 
                _setYawPitchRoll, _setAHRSData, _setAHRSPosData,
                _setRawData, _setBoardID, _setBoardState, _yawResetComplete
        """
        
        self.io_provider = io_provider
        self.update_rate_hz = update_rate_hz
        self.board_capabilities = board_capabilities
        self.notify_sink = notify_sink
        
        self.raw_data_update = IMUProtocol.GyroUpdate()
        self.ahrspos_update = AHRSProtocol.AHRSPosUpdate()
        self.board_state = _BoardState()
        self.board_id = _BoardId()
        
        self.last_update_time = 0
        self.byte_count = 0
        self.update_count = 0
        self.last_sensor_timestamp = 0
        self._stop = False
        
    def stop(self):
        self._stop = True
        
    def shutdown(self):
        self.io_provider.shutdown()
        
    def run(self):
        logger.info("NavX io thread starting")
        
        try:
            self.io_provider.init()
            
            # initial device configuration
            self.setUpdateRateHz(self.update_rate_hz)
            if not self.getConfiguration():
                logger.warning("-- Did not get configuration data")
            else:
                logger.info("-- Board is %s (rev %s)",
                            IMURegisters.model_type(self.board_id.type),
                            self.board_id.hw_rev)
                logger.info("-- Firmware %s.%s", self.board_id.fw_ver_major,
                                                 self.board_id.fw_ver_minor)
            
            log_error = True
            
            # Calculate delay to match configured update rate
            # Note:  some additional time is removed from the
            # 1/update_rate value to ensure samples are not
            # dropped, esp. at higher update rates.
            update_rate = 1.0/(self.update_rate_hz & 0xFF)
            if update_rate > DELAY_OVERHEAD_SECONDS:
                update_rate -= DELAY_OVERHEAD_SECONDS
                
            logger.info("-- Update rate: %shz (%.4fs)",
                        self.update_rate_hz, update_rate)
            
            # IO Loop
            while not self._stop:
                if self.board_state.update_rate_hz != self.update_rate_hz:
                    self.setUpdateRateHz(self.update_rate_hz)
                
                try:
                    self.getCurrentData()
                except IOError:
                    if log_error:
                        logger.exception("Error getting data")
                        log_error = False
                else:
                    log_error = True
                    
                    
                Timer.delay(update_rate)
        except Exception:
            logger.exception("Unhandled exception in NavX thread")
        finally:
            logger.info("NavX i/o thread exiting")
            
    def getConfiguration(self):
        success = False
        retry_count = 0
        
        while retry_count < 5 and not success:
            try:
                config = self.io_provider.read(IMURegisters.NAVX_REG_WHOAMI,
                                               IMURegisters.NAVX_REG_SENSOR_STATUS_H+1)
            except IOError as e:
                logger.warning("Error reading configuration data, retrying (%s)", e)
                success = False
                Timer.delay(0.5)
            else:
                board_id = self.board_id
                board_id.hw_rev                 = config[IMURegisters.NAVX_REG_HW_REV]
                board_id.fw_ver_major           = config[IMURegisters.NAVX_REG_FW_VER_MAJOR]
                board_id.fw_ver_minor           = config[IMURegisters.NAVX_REG_FW_VER_MINOR]
                board_id.type                   = config[IMURegisters.NAVX_REG_WHOAMI]
                self.notify_sink._setBoardID(board_id)
                
                board_state = self.board_state
                board_state.cal_status          = config[IMURegisters.NAVX_REG_CAL_STATUS]
                board_state.op_status           = config[IMURegisters.NAVX_REG_OP_STATUS]
                board_state.selftest_status     = config[IMURegisters.NAVX_REG_SELFTEST_STATUS]
                board_state.sensor_status       = AHRSProtocol.decodeBinaryUint16(config,IMURegisters.NAVX_REG_SENSOR_STATUS_L)
                board_state.gyro_fsr_dps        = AHRSProtocol.decodeBinaryUint16(config,IMURegisters.NAVX_REG_GYRO_FSR_DPS_L)
                board_state.accel_fsr_g         = config[IMURegisters.NAVX_REG_ACCEL_FSR_G]
                board_state.update_rate_hz      = config[IMURegisters.NAVX_REG_UPDATE_RATE_HZ]
                board_state.capability_flags    = AHRSProtocol.decodeBinaryUint16(config,IMURegisters.NAVX_REG_CAPABILITY_FLAGS_L)
                self.notify_sink._setBoardState(board_state)
                success = True
        
            retry_count += 1
        
        return success
    
    def getCurrentData(self):
        first_address = IMURegisters.NAVX_REG_UPDATE_RATE_HZ
        displacement_registers = self.board_capabilities._isDisplacementSupported()
        
        # If firmware supports displacement data, acquire it - otherwise implement
        # similar (but potentially less accurate) calculations on this processor.
        if displacement_registers:
            read_count = IMURegisters.NAVX_REG_LAST + 1 - first_address
        else:
            read_count = IMURegisters.NAVX_REG_QUAT_OFFSET_Z_H + 1 - first_address
        
        curr_data = self.io_provider.read(first_address, read_count)
    
        sensor_timestamp               = AHRSProtocol.decodeBinaryUint32(curr_data, IMURegisters.NAVX_REG_TIMESTAMP_L_L-first_address)
        if sensor_timestamp == self.last_sensor_timestamp:
            return
        
        self.last_sensor_timestamp = sensor_timestamp
        
        ahrspos_update = self.ahrspos_update
        ahrspos_update.op_status       = curr_data[IMURegisters.NAVX_REG_OP_STATUS - first_address]
        ahrspos_update.selftest_status = curr_data[IMURegisters.NAVX_REG_SELFTEST_STATUS - first_address]
        ahrspos_update.cal_status      = curr_data[IMURegisters.NAVX_REG_CAL_STATUS]
        ahrspos_update.sensor_status   = curr_data[IMURegisters.NAVX_REG_SENSOR_STATUS_L - first_address]
        ahrspos_update.yaw             = AHRSProtocol.decodeProtocolSignedHundredthsFloat(curr_data, IMURegisters.NAVX_REG_YAW_L-first_address)
        ahrspos_update.pitch           = AHRSProtocol.decodeProtocolSignedHundredthsFloat(curr_data, IMURegisters.NAVX_REG_PITCH_L-first_address)
        ahrspos_update.roll            = AHRSProtocol.decodeProtocolSignedHundredthsFloat(curr_data, IMURegisters.NAVX_REG_ROLL_L-first_address)
        ahrspos_update.compass_heading = AHRSProtocol.decodeProtocolUnsignedHundredthsFloat(curr_data, IMURegisters.NAVX_REG_HEADING_L-first_address)
        ahrspos_update.mpu_temp_c      = AHRSProtocol.decodeProtocolSignedHundredthsFloat(curr_data, IMURegisters.NAVX_REG_MPU_TEMP_C_L - first_address)
        ahrspos_update.world_linear_accel_x  = AHRSProtocol.decodeProtocolSignedThousandthsFloat(curr_data, IMURegisters.NAVX_REG_LINEAR_ACC_X_L-first_address)
        ahrspos_update.world_linear_accel_y  = AHRSProtocol.decodeProtocolSignedThousandthsFloat(curr_data, IMURegisters.NAVX_REG_LINEAR_ACC_Y_L-first_address)
        ahrspos_update.world_linear_accel_z  = AHRSProtocol.decodeProtocolSignedThousandthsFloat(curr_data, IMURegisters.NAVX_REG_LINEAR_ACC_Z_L-first_address)
        ahrspos_update.altitude        = AHRSProtocol.decodeProtocol1616Float(curr_data, IMURegisters.NAVX_REG_ALTITUDE_D_L - first_address)
        ahrspos_update.baro_pressure   = AHRSProtocol.decodeProtocol1616Float(curr_data, IMURegisters.NAVX_REG_PRESSURE_DL - first_address)
        ahrspos_update.fused_heading   = AHRSProtocol.decodeProtocolUnsignedHundredthsFloat(curr_data, IMURegisters.NAVX_REG_FUSED_HEADING_L-first_address)
        ahrspos_update.quaternionW     = AHRSProtocol.decodeBinaryInt16(curr_data, IMURegisters.NAVX_REG_QUAT_W_L-first_address)/ 32768.0
        ahrspos_update.quaternionX     = AHRSProtocol.decodeBinaryInt16(curr_data, IMURegisters.NAVX_REG_QUAT_X_L-first_address)/ 32768.0
        ahrspos_update.quaternionY     = AHRSProtocol.decodeBinaryInt16(curr_data, IMURegisters.NAVX_REG_QUAT_Y_L-first_address)/ 32768.0
        ahrspos_update.quaternionZ     = AHRSProtocol.decodeBinaryInt16(curr_data, IMURegisters.NAVX_REG_QUAT_Z_L-first_address)/ 32768.0
        if displacement_registers:
            ahrspos_update.vel_x       = AHRSProtocol.decodeProtocol1616Float(curr_data, IMURegisters.NAVX_REG_VEL_X_I_L-first_address)
            ahrspos_update.vel_y       = AHRSProtocol.decodeProtocol1616Float(curr_data, IMURegisters.NAVX_REG_VEL_Y_I_L-first_address)
            ahrspos_update.vel_z       = AHRSProtocol.decodeProtocol1616Float(curr_data, IMURegisters.NAVX_REG_VEL_Z_I_L-first_address)
            ahrspos_update.disp_x      = AHRSProtocol.decodeProtocol1616Float(curr_data, IMURegisters.NAVX_REG_DISP_X_I_L-first_address)
            ahrspos_update.disp_y      = AHRSProtocol.decodeProtocol1616Float(curr_data, IMURegisters.NAVX_REG_DISP_Y_I_L-first_address)
            ahrspos_update.disp_z      = AHRSProtocol.decodeProtocol1616Float(curr_data, IMURegisters.NAVX_REG_DISP_Z_I_L-first_address)            
             
            self.notify_sink._setAHRSPosData(ahrspos_update, sensor_timestamp)
        else:
            self.notify_sink._setAHRSData(ahrspos_update, sensor_timestamp)
        
        board_state = self.board_state
        board_state.cal_status      = curr_data[IMURegisters.NAVX_REG_CAL_STATUS-first_address]
        board_state.op_status       = curr_data[IMURegisters.NAVX_REG_OP_STATUS-first_address]
        board_state.selftest_status = curr_data[IMURegisters.NAVX_REG_SELFTEST_STATUS-first_address]
        board_state.sensor_status   = AHRSProtocol.decodeBinaryUint16(curr_data,IMURegisters.NAVX_REG_SENSOR_STATUS_L-first_address)
        board_state.update_rate_hz  = curr_data[IMURegisters.NAVX_REG_UPDATE_RATE_HZ-first_address]
        board_state.gyro_fsr_dps    = AHRSProtocol.decodeBinaryUint16(curr_data,IMURegisters.NAVX_REG_GYRO_FSR_DPS_L)
        board_state.accel_fsr_g     = curr_data[IMURegisters.NAVX_REG_ACCEL_FSR_G]
        board_state.capability_flags= AHRSProtocol.decodeBinaryUint16(curr_data,IMURegisters.NAVX_REG_CAPABILITY_FLAGS_L-first_address)
        self.notify_sink._setBoardState(board_state)
        
        raw_data_update = self.raw_data_update
        raw_data_update.raw_gyro_x      = AHRSProtocol.decodeBinaryInt16(curr_data,  IMURegisters.NAVX_REG_GYRO_X_L-first_address)
        raw_data_update.raw_gyro_y      = AHRSProtocol.decodeBinaryInt16(curr_data,  IMURegisters.NAVX_REG_GYRO_Y_L-first_address)
        raw_data_update.raw_gyro_z      = AHRSProtocol.decodeBinaryInt16(curr_data,  IMURegisters.NAVX_REG_GYRO_Z_L-first_address)
        raw_data_update.raw_accel_x     = AHRSProtocol.decodeBinaryInt16(curr_data,  IMURegisters.NAVX_REG_ACC_X_L-first_address)
        raw_data_update.raw_accel_y     = AHRSProtocol.decodeBinaryInt16(curr_data,  IMURegisters.NAVX_REG_ACC_Y_L-first_address)
        raw_data_update.raw_accel_z     = AHRSProtocol.decodeBinaryInt16(curr_data,  IMURegisters.NAVX_REG_ACC_Z_L-first_address)
        raw_data_update.cal_mag_x       = AHRSProtocol.decodeBinaryInt16(curr_data,  IMURegisters.NAVX_REG_MAG_X_L-first_address)
        raw_data_update.cal_mag_y       = AHRSProtocol.decodeBinaryInt16(curr_data,  IMURegisters.NAVX_REG_MAG_Y_L-first_address)
        raw_data_update.cal_mag_z       = AHRSProtocol.decodeBinaryInt16(curr_data,  IMURegisters.NAVX_REG_MAG_Z_L-first_address)
        raw_data_update.mpu_temp_c      = ahrspos_update.mpu_temp
        self.notify_sink._setRawData(raw_data_update, sensor_timestamp)
        
        self.last_update_time = Timer.getFPGATimestamp()
        self.byte_count += len(curr_data)
        self.update_count += 1
        
    def isConnected(self):
        time_since_last_update = Timer.getFPGATimestamp() - self.last_update_time
        return time_since_last_update <= IO_TIMEOUT_SECONDS
    
    def getByteCount(self):
        return self.byte_count
    
    def getUpdateCount(self):
        return self.update_count
    
    def setUpdateRateHz(self, update_rate_hz):
        self.io_provider.write(IMURegisters.NAVX_REG_UPDATE_RATE_HZ, update_rate_hz)
    
    def zeroYaw(self):
        self.io_provider.write( IMURegisters.NAVX_REG_INTEGRATION_CTL, 
                                   AHRSProtocol.NAVX_INTEGRATION_CTL_RESET_YAW )
        self.notify_sink._yawResetComplete()

    def zeroDisplacement(self):
        self.io_provider.write( IMURegisters.NAVX_REG_INTEGRATION_CTL, 
                                (AHRSProtocol.NAVX_INTEGRATION_CTL_RESET_DISP_X |
                                 AHRSProtocol.NAVX_INTEGRATION_CTL_RESET_DISP_Y |
                                 AHRSProtocol.NAVX_INTEGRATION_CTL_RESET_DISP_Z ) )       
