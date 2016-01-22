#----------------------------------------------------------------------------
# Copyright (c) Kauai Labs 2015. All Rights Reserved.
#
# Created in support of Team 2465 (Kauaibots).  Go Purple Wave!
#
# Open Source Software - may be modified and shared by FRC teams. Any
# modifications to this code must be accompanied by the \License.txt file
# in the root directory of the project
#----------------------------------------------------------------------------

from .imuprotocol import IMUProtocol

class AHRSProtocol(IMUProtocol):
    
    
    # NAVX_CAL_STATUS 

    NAVX_CAL_STATUS_IMU_CAL_STATE_MASK =          0x03
    NAVX_CAL_STATUS_IMU_CAL_INPROGRESS =          0x00
    NAVX_CAL_STATUS_IMU_CAL_ACCUMULATE =          0x01
    NAVX_CAL_STATUS_IMU_CAL_COMPLETE =            0x02

    NAVX_CAL_STATUS_MAG_CAL_COMPLETE =            0x04
    NAVX_CAL_STATUS_BARO_CAL_COMPLETE =           0x08

    # NAVX_SELFTEST_STATUS 

    NAVX_SELFTEST_STATUS_COMPLETE = 0x80

    NAVX_SELFTEST_RESULT_GYRO_PASSED =            0x01
    NAVX_SELFTEST_RESULT_ACCEL_PASSED =           0x02
    NAVX_SELFTEST_RESULT_MAG_PASSED =             0x04
    NAVX_SELFTEST_RESULT_BARO_PASSED =            0x08

    # NAVX_OP_STATUS 

    NAVX_OP_STATUS_INITIALIZING =                 0x00
    NAVX_OP_STATUS_SELFTEST_IN_PROGRESS =         0x01
    NAVX_OP_STATUS_ERROR =                        0x02
    NAVX_OP_STATUS_IMU_AUTOCAL_IN_PROGRESS =      0x03
    NAVX_OP_STATUS_NORMAL =                       0x04

    # NAVX_SENSOR_STATUS 
    NAVX_SENSOR_STATUS_MOVING =                   0x01
    NAVX_SENSOR_STATUS_YAW_STABLE =               0x02
    NAVX_SENSOR_STATUS_MAG_DISTURBANCE =          0x04
    NAVX_SENSOR_STATUS_ALTITUDE_VALID =           0x08
    NAVX_SENSOR_STATUS_SEALEVEL_PRESS_SET =       0x10
    NAVX_SENSOR_STATUS_FUSED_HEADING_VALID =      0x20
    
    # NAVX_REG_CAPABILITY_FLAGS (Aligned w/NAV6 Flags, see IMUProtocol.h) 

    NAVX_CAPABILITY_FLAG_OMNIMOUNT =             0x0004
    NAVX_CAPABILITY_FLAG_OMNIMOUNT_CONFIG_MASK = 0x0038
    NAVX_CAPABILITY_FLAG_VEL_AND_DISP =          0x0040
    NAVX_CAPABILITY_FLAG_YAW_RESET =             0x0080

    # NAVX_OMNIMOUNT_CONFIG 

    OMNIMOUNT_DEFAULT =                       0 # Same as Y_Z_UP 
    OMNIMOUNT_YAW_X_UP =                      1
    OMNIMOUNT_YAW_X_DOWN =                    2
    OMNIMOUNT_YAW_Y_UP =                      3
    OMNIMOUNT_YAW_Y_DOWN =                    4
    OMNIMOUNT_YAW_Z_UP =                      5
    OMNIMOUNT_YAW_Z_DOWN =                    6

    # NAVX_INTEGRATION_CTL 

    NAVX_INTEGRATION_CTL_RESET_VEL_X =        0x01
    NAVX_INTEGRATION_CTL_RESET_VEL_Y =        0x02
    NAVX_INTEGRATION_CTL_RESET_VEL_Z =        0x04
    NAVX_INTEGRATION_CTL_RESET_DISP_X =       0x08
    NAVX_INTEGRATION_CTL_RESET_DISP_Y =       0x10
    NAVX_INTEGRATION_CTL_RESET_DISP_Z =       0x20
    NAVX_INTEGRATION_CTL_RESET_YAW =          0x80
    
    class AHRS_TUNING_VAR_ID:
        UNSPECIFIED =                  0
        MOTION_THRESHOLD =             1 # In G 
        YAW_STABLE_THRESHOLD =         2 # In Degrees 
        MAG_DISTURBANCE_THRESHOLD =    3 # Ratio 
        SEA_LEVEL_PRESSURE =           4 # Millibars 
    
    
    class AHRS_DATA_TYPE:
        TUNING_VARIABLE =  0
        MAG_CALIBRATION =  1
        BOARD_IDENTITY =   2

    class AHRS_DATA_ACTION:
        DATA_GET = 0
        DATA_SET = 1

    BINARY_PACKET_INDICATOR_CHAR = '#'

    # AHRS Protocol encodes certain data in binary format, unlike the IMU  
    # protocol, which encodes all data in ASCII characters.  Thus, the     
    # packet start and message termination sequences may occur within the  
    # message content itself.  To support the binary format, the binary    
    # message has this format:                                             
    #                                                                      
    # [start][binary indicator][len][msgid]<MESSAGE>[checksum][terminator] 
    #                                                                      
    # (The binary indicator and len are not present in the ASCII protocol) 
    #                                                                      
    # The [len] does not include the length of the start and binary        
    # indicator characters, but does include all other message items,      
    # including the checksum and terminator sequence.                      
 
    MSGID_AHRS_UPDATE = 'a'
    AHRS_UPDATE_YAW_VALUE_INDEX = 4  # Degrees.  Signed Hundredths 
    AHRS_UPDATE_PITCH_VALUE_INDEX = 6  # Degrees.  Signed Hundredeths 
    AHRS_UPDATE_ROLL_VALUE_INDEX = 8  # Degrees.  Signed Hundredths 
    AHRS_UPDATE_HEADING_VALUE_INDEX = 10  # Degrees.  Unsigned Hundredths 
    AHRS_UPDATE_ALTITUDE_VALUE_INDEX = 12 # Meters.   Signed 16:16 
    AHRS_UPDATE_FUSED_HEADING_VALUE_INDEX = 16 # Degrees.  Unsigned Hundredths 
    AHRS_UPDATE_LINEAR_ACCEL_X_VALUE_INDEX = 18 # Inst. G.  Signed Thousandths 
    AHRS_UPDATE_LINEAR_ACCEL_Y_VALUE_INDEX = 20 # Inst. G.  Signed Thousandths 
    AHRS_UPDATE_LINEAR_ACCEL_Z_VALUE_INDEX = 22 # Inst. G.  Signed Thousandths 
    AHRS_UPDATE_CAL_MAG_X_VALUE_INDEX = 24 # Int16 (Device Units) 
    AHRS_UPDATE_CAL_MAG_Y_VALUE_INDEX = 26 # Int16 (Device Units) 
    AHRS_UPDATE_CAL_MAG_Z_VALUE_INDEX = 28 # Int16 (Device Units) 
    AHRS_UPDATE_CAL_MAG_NORM_RATIO_VALUE_INDEX = 30 # Ratio.  Unsigned Hundredths 
    AHRS_UPDATE_CAL_MAG_SCALAR_VALUE_INDEX = 32 # Coefficient. Signed 16:16 
    AHRS_UPDATE_MPU_TEMP_VAUE_INDEX = 36 # Centigrade.  Signed Hundredths 
    AHRS_UPDATE_RAW_MAG_X_VALUE_INDEX = 38 # INT16 (Device Units 
    AHRS_UPDATE_RAW_MAG_Y_VALUE_INDEX = 40 # INT16 (Device Units 
    AHRS_UPDATE_RAW_MAG_Z_VALUE_INDEX = 42 # INT16 (Device Units 
    AHRS_UPDATE_QUAT_W_VALUE_INDEX = 44 # INT16 
    AHRS_UPDATE_QUAT_X_VALUE_INDEX = 46 # INT16 
    AHRS_UPDATE_QUAT_Y_VALUE_INDEX = 48 # INT16 
    AHRS_UPDATE_QUAT_Z_VALUE_INDEX = 50 # INT16     
    AHRS_UPDATE_BARO_PRESSURE_VALUE_INDEX = 52 # millibar.  Signed 16:16 
    AHRS_UPDATE_BARO_TEMP_VAUE_INDEX = 56 # Centigrade.  Signed  Hundredths 
    AHRS_UPDATE_OPSTATUS_VALUE_INDEX = 58 # NAVX_OP_STATUS_XXX 
    AHRS_UPDATE_SENSOR_STATUS_VALUE_INDEX = 59 # NAVX_SENSOR_STATUS_XXX 
    AHRS_UPDATE_CAL_STATUS_VALUE_INDEX    = 60 # NAVX_CAL_STATUS_XXX 
    AHRS_UPDATE_SELFTEST_STATUS_VALUE_INDEX = 61 # NAVX_SELFTEST_STATUS_XXX 
    AHRS_UPDATE_MESSAGE_CHECKSUM_INDEX = 62
    AHRS_UPDATE_MESSAGE_TERMINATOR_INDEX = 64
    AHRS_UPDATE_MESSAGE_LENGTH = 66

    # AHRSAndPositioning Update Packet (similar to AHRS, but removes magnetometer and adds velocity/displacement) 

    MSGID_AHRSPOS_UPDATE =             'p'
    AHRSPOS_UPDATE_YAW_VALUE_INDEX =           4 # Degrees.  Signed Hundredths 
    AHRSPOS_UPDATE_PITCH_VALUE_INDEX =         6 # Degrees.  Signed Hundredeths 
    AHRSPOS_UPDATE_ROLL_VALUE_INDEX =          8 # Degrees.  Signed Hundredths 
    AHRSPOS_UPDATE_HEADING_VALUE_INDEX =       10 # Degrees.  Unsigned Hundredths 
    AHRSPOS_UPDATE_ALTITUDE_VALUE_INDEX =      12 # Meters.   Signed 16:16 
    AHRSPOS_UPDATE_FUSED_HEADING_VALUE_INDEX = 16 # Degrees.  Unsigned Hundredths 
    AHRSPOS_UPDATE_LINEAR_ACCEL_X_VALUE_INDEX = 18 # Inst. G.  Signed Thousandths 
    AHRSPOS_UPDATE_LINEAR_ACCEL_Y_VALUE_INDEX = 20 # Inst. G.  Signed Thousandths 
    AHRSPOS_UPDATE_LINEAR_ACCEL_Z_VALUE_INDEX = 22 # Inst. G.  Signed Thousandths 
    AHRSPOS_UPDATE_VEL_X_VALUE_INDEX =         24 # Signed 16:16, in meters/sec 
    AHRSPOS_UPDATE_VEL_Y_VALUE_INDEX =         28 # Signed 16:16, in meters/sec 
    AHRSPOS_UPDATE_VEL_Z_VALUE_INDEX =         32 # Signed 16:16, in meters/sec 
    AHRSPOS_UPDATE_DISP_X_VALUE_INDEX =        36 # Signed 16:16, in meters 
    AHRSPOS_UPDATE_DISP_Y_VALUE_INDEX =        40 # Signed 16:16, in meters 
    AHRSPOS_UPDATE_DISP_Z_VALUE_INDEX =        44 # Signed 16:16, in meters 
    AHRSPOS_UPDATE_QUAT_W_VALUE_INDEX =        48 # INT16 
    AHRSPOS_UPDATE_QUAT_X_VALUE_INDEX =        50 # INT16 
    AHRSPOS_UPDATE_QUAT_Y_VALUE_INDEX =        52 # INT16 
    AHRSPOS_UPDATE_QUAT_Z_VALUE_INDEX =        54 # INT16 
    AHRSPOS_UPDATE_MPU_TEMP_VAUE_INDEX =       56 # Centigrade.  Signed Hundredths 
    AHRSPOS_UPDATE_OPSTATUS_VALUE_INDEX =      58 # NAVX_OP_STATUS_XXX 
    AHRSPOS_UPDATE_SENSOR_STATUS_VALUE_INDEX = 59 # NAVX_SENSOR_STATUS_XXX 
    AHRSPOS_UPDATE_CAL_STATUS_VALUE_INDEX =    60 # NAVX_CAL_STATUS_XXX 
    AHRSPOS_UPDATE_SELFTEST_STATUS_VALUE_INDEX    = 61 # NAVX_SELFTEST_STATUS_XXX 
    AHRSPOS_UPDATE_MESSAGE_CHECKSUM_INDEX =    62
    AHRSPOS_UPDATE_MESSAGE_TERMINATOR_INDEX =  64
    AHRSPOS_UPDATE_MESSAGE_LENGTH =            66
    
    # Data Get Request:  Tuning Variable, Mag Cal, Board Identity (Response message depends upon request type)
    MSGID_DATA_REQUEST =               'D'
    DATA_REQUEST_DATATYPE_VALUE_INDEX =        4
    DATA_REQUEST_VARIABLEID_VALUE_INDEX =      5
    DATA_REQUEST_CHECKSUM_INDEX =              6
    DATA_REQUEST_TERMINATOR_INDEX =            8
    DATA_REQUEST_MESSAGE_LENGTH =              10
    
    # Data Set Response Packet
    MSGID_DATA_SET_RESPONSE =          'v'
    DATA_SET_RESPONSE_DATATYPE_VALUE_INDEX =   4
    DATA_SET_RESPONSE_VARID_VALUE_INDEX =      5
    DATA_SET_RESPONSE_STATUS_VALUE_INDEX =     6
    DATA_SET_RESPONSE_MESSAGE_CHECKSUM_INDEX = 7
    DATA_SET_RESPONSE_MESSAGE_TERMINATOR_INDEX = 9
    DATA_SET_RESPONSE_MESSAGE_LENGTH =         11

    # Integration Control Command Packet 
    MSGID_INTEGRATION_CONTROL_CMD =    'I'
    INTEGRATION_CONTROL_CMD_ACTION_INDEX =     4
    INTEGRATION_CONTROL_CMD_PARAMETER_INDEX =  5
    INTEGRATION_CONTROL_CMD_MESSAGE_CHECKSUM_INDEX    = 9
    INTEGRATION_CONTROL_CMD_MESSAGE_TERMINATOR_INDEX = 11
    INTEGRATION_CONTROL_CMD_MESSAGE_LENGTH    =   13

    # Integration Control Response Packet 
    MSGID_INTEGRATION_CONTROL_RESP =   'i'
    INTEGRATION_CONTROL_RESP_ACTION_INDEX =    4
    INTEGRATION_CONTROL_RESP_PARAMETER_INDEX = 5
    INTEGRATION_CONTROL_RESP_MESSAGE_CHECKSUM_INDEX = 9
    INTEGRATION_CONTROL_RESP_MESSAGE_TERMINATOR_INDEX = 11
    INTEGRATION_CONTROL_RESP_MESSAGE_LENGTH =  13
    
    # Magnetometer Calibration Packet - e.g., !m[x_bias][y_bias][z_bias][m1,1 ... m3,3][cr][lf]
    MSGID_MAG_CAL_CMD =                'M'
    MAG_CAL_DATA_ACTION_VALUE_INDEX =          4
    MAG_X_BIAS_VALUE_INDEX =                   5 # signed short 
    MAG_Y_BIAS_VALUE_INDEX =                   7
    MAG_Z_BIAS_VALUE_INDEX =                   9
    MAG_XFORM_1_1_VALUE_INDEX =                11 # signed 16:16 
    MAG_XFORM_1_2_VALUE_INDEX =                15
    MAG_XFORM_1_3_VALUE_INDEX =                19
    MAG_XFORM_2_1_VALUE_INDEX =                23
    MAG_XFORM_2_2_VALUE_INDEX =                25
    MAG_XFORM_2_3_VALUE_INDEX =                31
    MAG_XFORM_3_1_VALUE_INDEX =                35
    MAG_XFORM_3_2_VALUE_INDEX =                39
    MAG_XFORM_3_3_VALUE_INDEX =                43
    MAG_CAL_EARTH_MAG_FIELD_NORM_VALUE_INDEX = 47
    MAG_CAL_CMD_MESSAGE_CHECKSUM_INDEX  =      51
    MAG_CAL_CMD_MESSAGE_TERMINATOR_INDEX =     53
    MAG_CAL_CMD_MESSAGE_LENGTH =               55

    # Tuning Variable Packet
    MSGID_FUSION_TUNING_CMD  =         'T'
    FUSION_TUNING_DATA_ACTION_VALUE_INDEX =    4
    FUSION_TUNING_CMD_VAR_ID_VALUE_INDEX =     5
    FUSION_TUNING_CMD_VAR_VALUE_INDEX =        6
    FUSION_TUNING_CMD_MESSAGE_CHECKSUM_INDEX = 10
    FUSION_TUNING_CMD_MESSAGE_TERMINATOR_INDEX = 12
    FUSION_TUNING_CMD_MESSAGE_LENGTH =         14

    # Board Identity Response Packet- e.g., !c[type][hw_rev][fw_major][fw_minor][unique_id[12]]
    MSGID_BOARD_IDENTITY_RESPONSE =    'i'
    BOARD_IDENTITY_BOARDTYPE_VALUE_INDEX =     4
    BOARD_IDENTITY_HWREV_VALUE_INDEX =         5
    BOARD_IDENTITY_FW_VER_MAJOR =              6
    BOARD_IDENTITY_FW_VER_MINOR =              7
    BOARD_IDENTITY_FW_VER_REVISION_VALUE_INDEX = 8
    BOARD_IDENTITY_UNIQUE_ID_0 =               10
    BOARD_IDENTITY_UNIQUE_ID_1 =               11
    BOARD_IDENTITY_UNIQUE_ID_2 =               12
    BOARD_IDENTITY_UNIQUE_ID_3 =               13
    BOARD_IDENTITY_UNIQUE_ID_4 =               14
    BOARD_IDENTITY_UNIQUE_ID_5 =               15
    BOARD_IDENTITY_UNIQUE_ID_6 =               16
    BOARD_IDENTITY_UNIQUE_ID_7 =               17
    BOARD_IDENTITY_UNIQUE_ID_8 =               18
    BOARD_IDENTITY_UNIQUE_ID_9 =               19
    BOARD_IDENTITY_UNIQUE_ID_10 =              20
    BOARD_IDENTITY_UNIQUE_ID_11 =              21
    BOARD_IDENTITY_RESPONSE_CHECKSUM_INDEX =   22
    BOARD_IDENTITY_RESPONSE_TERMINATOR_INDEX = 24
    BOARD_IDENTITY_RESPONSE_MESSAGE_LENGTH =   26

    MAX_BINARY_MESSAGE_LENGTH = AHRSPOS_UPDATE_MESSAGE_LENGTH

#     class AHRSUpdate:
#         yaw = 0.0
#         pitch = 0.0
#         roll = 0.0
#         compass_heading = 0.0
#         altitude = 0.0
#         fused_heading = 0.0
#         world_linear_accel_x = 0.0
#         world_linear_accel_y = 0.0
#         world_linear_accel_z = 0.0
#         cal_mag_x = 0
#         cal_mag_y = 0
#         cal_mag_z = 0
#         mag_field_norm_ratio = 0.0
#         mag_field_norm_scalar = 0.0
#         mpu_temp_c = 0.0
#         raw_mag_x = 0
#         raw_mag_y = 0
#         raw_mag_z = 0
#         quaternionW = 0
#         quaternionX = 0
#         quaternionY = 0
#         quaternionZ = 0
#         barometric_pressure = 0.0
#         baro_temp = 0.0
#         op_status = 0
#         sensor_status = 0
#         cal_status = 0
#         selftest_status = 0
        
    class AHRSPosUpdate:
        yaw = 0.0
        pitch = 0.0
        roll = 0.0
        compass_heading = 0.0
        altitude = 0.0
        fused_heading = 0.0
        world_linear_accel_x = 0.0
        world_linear_accel_y = 0.0
        world_linear_accel_z = 0.0
        vel_x = 0.0
        vel_y = 0.0
        vel_z = 0.0
        disp_x = 0.0
        disp_y = 0.0
        disp_z = 0.0
        mpu_temp = 0.0
        quaternionW = 0
        quaternionX = 0
        quaternionY = 0
        quaternionZ = 0
        barometric_pressure = 0.0
        baro_temp = 0.0
        op_status = 0
        sensor_status = 0
        cal_status = 0
        selftest_status = 0

    @staticmethod
    def decodeBinaryUint16(data, offset):
        return int.from_bytes(data[offset:offset+2], 'little', signed=False)
    
    @staticmethod
    def encodeBinaryUint16(i, data, offset):
        data[offset:offset+2] = i.to_bytes(2, 'little', signed=False)
    
    @staticmethod
    def decodeBinaryInt16(data, offset):
        return int.from_bytes(data[offset:offset+2], 'little', signed=True)
    
    @staticmethod
    def encodeBinaryInt16(i, data, offset):
        data[offset:offset+2] = i.to_bytes(2, 'little', signed=True)

    @staticmethod
    def decodeProtocol1616Float(data, offset):
        return int.from_bytes(data[offset:offset+4], 'little', signed=True)/65536.0
    
    @staticmethod
    def encodeProtocol1616Float(f, data, offset):
        data[offset:offset+4] = int(f*65536).to_bytes(4, 'little', signed=True)
    
    @staticmethod
    def decodeProtocolSignedHundredthsFloat(data, offset):
        return int.from_bytes(data[offset:offset+2], 'little', signed=True)/100.0
    
    @staticmethod
    def encodeProtocolSignedHundredthsFloat(f, data, offset):
        data[offset:offset+2] = int(f*100).to_bytes(2, 'little', signed=True)
    
    @staticmethod
    def decodeProtocolSignedThousandthsFloat(data, offset):
        return int.from_bytes(data[offset:offset+2], 'little', signed=True)/1000.0
    
    @staticmethod
    def encodeProtocolSignedThousandthsFloat(f, data, offset):
        data[offset:offset+2] = int(f*1000).to_bytes(2, 'little', signed=True)
    
    @staticmethod
    def decodeProtocolUnsignedHundredthsFloat(data, offset):
        return int.from_bytes(data[offset:offset+2], 'little', signed=False)/100.0
    
    @staticmethod
    def encodeProtocolUnsignedHundredthsFloat(f, data, offset):
        data[offset:offset+2] = int(f*100).to_bytes(2, 'little', signed=False)
