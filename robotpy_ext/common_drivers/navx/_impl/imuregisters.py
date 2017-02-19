# validated: 2017-02-19 DS fed66235acf0 java/navx/src/com/kauailabs/navx/IMURegisters.java
#----------------------------------------------------------------------------
# Copyright (c) Kauai Labs 2015. All Rights Reserved.
#
# Created in support of Team 2465 (Kauaibots).  Go Purple Wave!
#
# Open Source Software - may be modified and shared by FRC teams. Any
# modifications to this code must be accompanied by the \License.txt file
# in the root directory of the project
#----------------------------------------------------------------------------

class IMURegisters:
    
    #********************************************
    # Device Identification Registers            
    #********************************************

    NAVX_REG_WHOAMI               = 0x00 # NAVX_MODEL_XXX 
    NAVX_REG_HW_REV               = 0x01
    NAVX_REG_FW_VER_MAJOR         = 0x02
    NAVX_REG_FW_VER_MINOR         = 0x03
    
    # Model types
    NAVX_MODEL_NAVX_MXP           = 0x32
    
    @classmethod
    def model_type(cls, whoami):
        if whoami == cls.NAVX_MODEL_NAVX_MXP:
            return "NavX MXP"
        else:
            return "unknown"

    #********************************************
    # Status and Control Registers               
    #********************************************

    # Read-write 
    NAVX_REG_UPDATE_RATE_HZ      = 0x04 # Range:  4 - 50 [unsigned byte] 
    # Read-only 
    # Accelerometer Full-Scale Range:  in units of G [unsigned byte] 
    NAVX_REG_ACCEL_FSR_G         = 0x05
    # Gyro Full-Scale Range (Degrees/Sec):  Range:  250, 500, 1000 or 2000 [unsigned short] 
    NAVX_REG_GYRO_FSR_DPS_L      = 0x06 # Lower 8-bits of Gyro Full-Scale Range 
    NAVX_REG_GYRO_FSR_DPS_H      = 0x07 # Upper 8-bits of Gyro Full-Scale Range 
    NAVX_REG_OP_STATUS           = 0x08 # NAVX_OP_STATUS_XXX 
    NAVX_REG_CAL_STATUS          = 0x09 # NAVX_CAL_STATUS_XXX 
    NAVX_REG_SELFTEST_STATUS     = 0x0A # NAVX_SELFTEST_STATUS_XXX 
    NAVX_REG_CAPABILITY_FLAGS_L  = 0x0B
    NAVX_REG_CAPABILITY_FLAGS_H  = 0x0C

    #********************************************
    # Processed Data Registers                   
    #********************************************

    NAVX_REG_SENSOR_STATUS_L     = 0x10 # NAVX_SENSOR_STATUS_XXX 
    NAVX_REG_SENSOR_STATUS_H     = 0x11
    # Timestamp:  [unsigned long] 
    NAVX_REG_TIMESTAMP_L_L       = 0x12
    NAVX_REG_TIMESTAMP_L_H       = 0x13
    NAVX_REG_TIMESTAMP_H_L       = 0x14
    NAVX_REG_TIMESTAMP_H_H       = 0x15

    # Yaw, Pitch, Roll:  Range: -180.00 to 180.00 [signed hundredths] 
    # Compass Heading:   Range: 0.00 to 360.00 [unsigned hundredths] 
    # Altitude in Meters:  In units of meters [16:16] 

    NAVX_REG_YAW_L               = 0x16 # Lower 8 bits of Yaw     
    NAVX_REG_YAW_H               = 0x17 # Upper 8 bits of Yaw     
    NAVX_REG_ROLL_L              = 0x18 # Lower 8 bits of Roll    
    NAVX_REG_ROLL_H              = 0x19 # Upper 8 bits of Roll    
    NAVX_REG_PITCH_L             = 0x1A # Lower 8 bits of Pitch   
    NAVX_REG_PITCH_H             = 0x1B # Upper 8 bits of Pitch   
    NAVX_REG_HEADING_L           = 0x1C # Lower 8 bits of Heading 
    NAVX_REG_HEADING_H           = 0x1D # Upper 8 bits of Heading 
    NAVX_REG_FUSED_HEADING_L     = 0x1E # Upper 8 bits of Fused Heading 
    NAVX_REG_FUSED_HEADING_H     = 0x1F # Upper 8 bits of Fused Heading 
    NAVX_REG_ALTITUDE_I_L        = 0x20
    NAVX_REG_ALTITUDE_I_H        = 0x21
    NAVX_REG_ALTITUDE_D_L        = 0x22
    NAVX_REG_ALTITUDE_D_H        = 0x23

    # World-frame Linear Acceleration: In units of +/- G * 1000 [signed thousandths] 

    NAVX_REG_LINEAR_ACC_X_L    = 0x24 # Lower 8 bits of Linear Acceleration X 
    NAVX_REG_LINEAR_ACC_X_H    = 0x25 # Upper 8 bits of Linear Acceleration X 
    NAVX_REG_LINEAR_ACC_Y_L    = 0x26 # Lower 8 bits of Linear Acceleration Y 
    NAVX_REG_LINEAR_ACC_Y_H    = 0x27 # Upper 8 bits of Linear Acceleration Y 
    NAVX_REG_LINEAR_ACC_Z_L    = 0x28 # Lower 8 bits of Linear Acceleration Z 
    NAVX_REG_LINEAR_ACC_Z_H    = 0x29 # Upper 8 bits of Linear Acceleration Z 

    # Quaternion:  Range -1 to 1 [signed short ratio] 

    NAVX_REG_QUAT_W_L             = 0x2A # Lower 8 bits of Quaternion W 
    NAVX_REG_QUAT_W_H             = 0x2B # Upper 8 bits of Quaternion W 
    NAVX_REG_QUAT_X_L             = 0x2C # Lower 8 bits of Quaternion X 
    NAVX_REG_QUAT_X_H             = 0x2D # Upper 8 bits of Quaternion X 
    NAVX_REG_QUAT_Y_L             = 0x2E # Lower 8 bits of Quaternion Y 
    NAVX_REG_QUAT_Y_H             = 0x2F # Upper 8 bits of Quaternion Y 
    NAVX_REG_QUAT_Z_L             = 0x30 # Lower 8 bits of Quaternion Z 
    NAVX_REG_QUAT_Z_H             = 0x31 # Upper 8 bits of Quaternion Z 

    #********************************************
    # Raw Data Registers                         
    #********************************************

    # Sensor Die Temperature:  Range +/- 150, In units of Centigrade * 100 [signed hundredths float 

    NAVX_REG_MPU_TEMP_C_L        = 0x32 # Lower 8 bits of Temperature 
    NAVX_REG_MPU_TEMP_C_H        = 0x33 # Upper 8 bits of Temperature 

    # Raw, Calibrated Angular Rotation, in device units.  Value in DPS = units / GYRO_FSR_DPS [signed short] 

    NAVX_REG_GYRO_X_L            = 0x34
    NAVX_REG_GYRO_X_H            = 0x35
    NAVX_REG_GYRO_Y_L            = 0x36
    NAVX_REG_GYRO_Y_H            = 0x37
    NAVX_REG_GYRO_Z_L            = 0x38
    NAVX_REG_GYRO_Z_H            = 0x39

    # Raw, Calibrated, Acceleration Data, in device units.  Value in G = units / ACCEL_FSR_G [signed short] 

    NAVX_REG_ACC_X_L            = 0x3A
    NAVX_REG_ACC_X_H            = 0x3B
    NAVX_REG_ACC_Y_L            = 0x3C
    NAVX_REG_ACC_Y_H            = 0x3D
    NAVX_REG_ACC_Z_L            = 0x3E
    NAVX_REG_ACC_Z_H            = 0x3F

    # Raw, Calibrated, Un-tilt corrected Magnetometer Data, in device units.  1 unit = 0.15 uTesla [signed short] 

    NAVX_REG_MAG_X_L            = 0x40
    NAVX_REG_MAG_X_H            = 0x41
    NAVX_REG_MAG_Y_L            = 0x42
    NAVX_REG_MAG_Y_H            = 0x43
    NAVX_REG_MAG_Z_L            = 0x44
    NAVX_REG_MAG_Z_H            = 0x45

    # Calibrated Pressure in millibars Valid Range:  10.00 Max:  1200.00 [16:16 float]  

    NAVX_REG_PRESSURE_IL       = 0x46
    NAVX_REG_PRESSURE_IH       = 0x47
    NAVX_REG_PRESSURE_DL       = 0x48
    NAVX_REG_PRESSURE_DH       = 0x49

    # Pressure Sensor Die Temperature:  Range +/- 150.00C [signed hundredths] 

    NAVX_REG_PRESSURE_TEMP_L    = 0x4A
    NAVX_REG_PRESSURE_TEMP_H    = 0x4B

    #********************************************
    # Calibration Registers                      
    #********************************************

    # Yaw Offset: Range -180.00 to 180.00 [signed hundredths] 

    NAVX_REG_YAW_OFFSET_L        = 0x4C # Lower 8 bits of Yaw Offset 
    NAVX_REG_YAW_OFFSET_H        = 0x4D # Upper 8 bits of Yaw Offset 

    # Quaternion Offset:  Range: -1 to 1 [signed short ratio]  

    NAVX_REG_QUAT_OFFSET_W_L     = 0x4E # Lower 8 bits of Quaternion W 
    NAVX_REG_QUAT_OFFSET_W_H     = 0x4F # Upper 8 bits of Quaternion W 
    NAVX_REG_QUAT_OFFSET_X_L     = 0x50 # Lower 8 bits of Quaternion X 
    NAVX_REG_QUAT_OFFSET_X_H     = 0x51 # Upper 8 bits of Quaternion X 
    NAVX_REG_QUAT_OFFSET_Y_L     = 0x52 # Lower 8 bits of Quaternion Y 
    NAVX_REG_QUAT_OFFSET_Y_H     = 0x53 # Upper 8 bits of Quaternion Y 
    NAVX_REG_QUAT_OFFSET_Z_L     = 0x54 # Lower 8 bits of Quaternion Z 
    NAVX_REG_QUAT_OFFSET_Z_H     = 0x55 # Upper 8 bits of Quaternion Z 

    #********************************************
    # Integrated Data Registers                  
    #********************************************

    # Integration Control (Write-Only)           
    NAVX_REG_INTEGRATION_CTL   = 0x56
    NAVX_REG_PAD_UNUSED        = 0x57

    # Velocity:  Range -32768.9999 - 32767.9999 in units of Meters/Sec      

    NAVX_REG_VEL_X_I_L         = 0x58
    NAVX_REG_VEL_X_I_H         = 0x59
    NAVX_REG_VEL_X_D_L         = 0x5A
    NAVX_REG_VEL_X_D_H         = 0x5B
    NAVX_REG_VEL_Y_I_L         = 0x5C
    NAVX_REG_VEL_Y_I_H         = 0x5D
    NAVX_REG_VEL_Y_D_L         = 0x5E
    NAVX_REG_VEL_Y_D_H         = 0x5F
    NAVX_REG_VEL_Z_I_L         = 0x60
    NAVX_REG_VEL_Z_I_H         = 0x61
    NAVX_REG_VEL_Z_D_L         = 0x62
    NAVX_REG_VEL_Z_D_H         = 0x63

    # Displacement:  Range -32768.9999 - 32767.9999 in units of Meters      

    NAVX_REG_DISP_X_I_L        = 0x64
    NAVX_REG_DISP_X_I_H        = 0x65
    NAVX_REG_DISP_X_D_L        = 0x66
    NAVX_REG_DISP_X_D_H        = 0x67
    NAVX_REG_DISP_Y_I_L        = 0x68
    NAVX_REG_DISP_Y_I_H        = 0x69
    NAVX_REG_DISP_Y_D_L        = 0x6A
    NAVX_REG_DISP_Y_D_H        = 0x6B
    NAVX_REG_DISP_Z_I_L        = 0x6C
    NAVX_REG_DISP_Z_I_H        = 0x6D
    NAVX_REG_DISP_Z_D_L        = 0x6E
    NAVX_REG_DISP_Z_D_H        = 0x6F
    
    NAVX_REG_LAST = NAVX_REG_DISP_Z_D_H
