# validated: 2017-02-19 DS 45685cfce2a1 roborio/java/navx_frc/src/com/kauailabs/navx/frc/AHRS.java
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

import wpilib
from wpilib.interfaces import PIDSource

from ._impl import AHRSProtocol

from .continuousangletracker import ContinuousAngleTracker
from .inertialdataintegrator import InertialDataIntegrator
from .offsettracker import OffsetTracker

from .registerio import RegisterIO
from .registerio_i2c import RegisterIO_I2C
from .registerio_spi import RegisterIO_SPI

import logging
logger = logging.getLogger('navx')

__all__ = ['AHRS']


DEV_UNITS_MAX = 32768.0
UTESLA_PER_DEV_UNIT = 0.15

class AHRS(wpilib.SensorBase):
    """The AHRS class provides an interface to AHRS capabilities
    of the KauaiLabs navX Robotics Navigation Sensor via SPI and I2C
    communications interfaces on the RoboRIO.
    
    The AHRS class enables access to basic connectivity and state information,
    as well as key 6-axis and 9-axis orientation information (yaw, pitch, roll,
    compass heading, fused (9-axis) heading and magnetic disturbance detection.
    
    Additionally, the ARHS class also provides access to extended information
    including linear acceleration, motion detection, rotation detection and sensor
    temperature.
    
    If used with the navX Aero, the AHRS class also provides access to
    altitude, barometric pressure and pressure sensor temperature data
    
    .. note:: This implementation does not provide access to the NavX via
              a serial port
    """
    
    NAVX_DEFAULT_UPDATE_RATE_HZ         = 60
    YAW_HISTORY_LENGTH                  = 10
    DEFAULT_ACCEL_FSR_G                 = 2
    DEFAULT_GYRO_FSR_DPS                = 2000
    
    PIDSourceType = PIDSource.PIDSourceType
    
    @classmethod
    def create_spi(cls, port=wpilib.SPI.Port.kMXP, spi_bitrate=None, update_rate_hz=None):
        """Constructs the AHRS class using SPI communication, overriding the 
        default update rate with a custom rate which may be from 4 to 100, 
        representing the number of updates per second sent by the sensor.  
        
        This constructor allows the specification of a custom SPI bitrate, in bits/second.
        
        .. note:: Increasing the update rate may increase the CPU utilization.
        
        :param port: SPI Port to use
        :type port: :class:`.SPI.Port`
        :param spi_bitrate: SPI bitrate (Maximum:  2,000,000)
        :param update_rate_hz: Custom Update Rate (Hz)
        """
        
        io = RegisterIO_SPI(port, spi_bitrate)
        return AHRS(io, update_rate_hz)
    
    @classmethod
    def create_i2c(cls, port=wpilib.I2C.Port.kMXP, update_rate_hz=None):
        """Constructs the AHRS class using I2C communication, overriding the
        default update rate with a custom rate which may be from 4 to 100,
        representing the number of updates per second sent by the sensor.
        
        This constructor should be used if communicating via I2C.
        
        .. note:: Increasing the update rate may increase the CPU utilization.
        
        :param port: I2C Port to use
        :type port: :class:`.I2C.Port`
        :param update_rate_hz: Custom Update Rate (Hz)
        """
        
        io = RegisterIO_I2C(port)
        return AHRS(io, update_rate_hz)
    
    def __init__(self, io, update_rate_hz=None):
        """Don't use the constructor, use the :meth:`create_spi` or
        :meth:`create_i2c` class methods instead"""
        
        if update_rate_hz is None:
            update_rate_hz = self.NAVX_DEFAULT_UPDATE_RATE_HZ
        
        # Internal variables
        
        self.yaw = 0
        self.pitch = 0
        self.roll = 0
        self.compass_heading = 0
        self.world_linear_accel_x = 0
        self.world_linear_accel_y = 0
        self.world_linear_accel_z = 0
        self.mpu_temp_c = 0
        self.fused_heading = 0
        self.altitude = 0
        self.baro_pressure = 0
        #self.is_moving = False
        #self.is_rotating = False
        self.baro_sensor_temp_c = 0
        #self.altitude_valid = False
        #self.is_magnetometer_calibrated = False
        #self.magnetic_disturbance = False
        self.quaternionW = 0
        self.quaternionX = 0
        self.quaternionY = 0
        self.quaternionZ = 0       
        
        # Integrated Data 
        self.vel_x = 0
        self.vel_y = 0
        self.vel_z = 0
        self.disp_x = 0
        self.disp_y = 0
        self.disp_z = 0
        
        # Raw Data
        self.raw_gyro_x = 0
        self.raw_gyro_y = 0
        self.raw_gyro_z = 0
        self.raw_accel_x = 0
        self.raw_accel_y = 0
        self.raw_accel_z = 0
        self.cal_mag_x = 0
        self.cal_mag_y = 0
        self.cal_mag_z = 0
        
        # Configuration/Status
        self.update_rate_hz = update_rate_hz
        self.accel_fsr_g = self.DEFAULT_ACCEL_FSR_G
        self.gyro_fsr_dps = self.DEFAULT_GYRO_FSR_DPS
        self.capability_flags = 0    
        self.op_status = 0
        self.sensor_status = 0
        self.cal_status = 0
        self.selftest_status = 0
        
        # Board ID 
        self.board_type = 0
        self.hw_rev = 0
        self.fw_ver_major = 0
        self.fw_ver_minor = 0
        
        self.last_sensor_timestamp = 0
        self.last_update_time = 0
        
        self.pidSource = self.PIDSourceType.kDisplacement
        
        self.mutex = threading.RLock()
        
        self.integrator = InertialDataIntegrator()
        self.yaw_offset_tracker = OffsetTracker(self.YAW_HISTORY_LENGTH)
        self.yaw_angle_tracker = ContinuousAngleTracker()
        self.callbacks = []
        
        self.io = RegisterIO(io, self.update_rate_hz, self, self)
        self.ioThread = threading.Thread(target=self.io.run, name='NavX',
                                         daemon=True)
        
        self.ioThread.start()
        
        # Need this to free on unit test wpilib reset
        wpilib.Resource._add_global_resource(self)
    
    
    def free(self):
        self.io.stop()
        try:
            self.ioThread.join(timeout=5)
        finally:
            self.io.shutdown()
    
    # calculated properties
    @property
    def is_moving(self):
        return (self.sensor_status & AHRSProtocol.NAVX_SENSOR_STATUS_MOVING) != 0
    
    @property
    def is_rotating(self):
        return (self.sensor_status & AHRSProtocol.NAVX_SENSOR_STATUS_YAW_STABLE) == 0
    
    @property
    def altitude_valid(self):
        return (self.sensor_status & AHRSProtocol.NAVX_SENSOR_STATUS_ALTITUDE_VALID) != 0
    
    @property
    def is_magnetometer_calibrated(self):
        return (self.sensor_status & AHRSProtocol.NAVX_CAL_STATUS_MAG_CAL_COMPLETE) != 0
    
    @property
    def magnetic_disturbance(self):
        return (self.sensor_status & AHRSProtocol.NAVX_SENSOR_STATUS_MAG_DISTURBANCE) != 0
    #
    # Public API
    #
    
    def getPitch(self):
        """Returns the current pitch value (in degrees, from -180 to 180)
        reported by the sensor.  Pitch is a measure of rotation around
        the X Axis.
        
        :returns: The current pitch value in degrees (-180 to 180).
        """
        return self.pitch

    
    def getRoll(self):
        """Returns the current roll value (in degrees, from -180 to 180)
        reported by the sensor.  Roll is a measure of rotation around
        the X Axis.
        
        :returns: The current roll value in degrees (-180 to 180).
        """
        return self.roll

    def getYaw(self):
        """Returns the current yaw value (in degrees, from -180 to 180)
        reported by the sensor.  Yaw is a measure of rotation around
        the Z Axis (which is perpendicular to the earth).
        
        Note that the returned yaw value will be offset by a user-specified
        offset value this user-specified offset value is set by
        invoking the zeroYaw() method.
        
        :returns: The current yaw value in degrees (-180 to 180).
        """
        if self._isBoardYawResetSupported():
            return self.yaw
        else:
            return self.yaw_offset_tracker.applyOffset(self.yaw)

    def getCompassHeading(self):
        """Returns the current tilt-compensated compass heading
        value (in degrees, from 0 to 360) reported by the sensor.
        
        Note that this value is sensed by a magnetometer,
        which can be affected by nearby magnetic fields (e.g., the
        magnetic fields generated by nearby motors).
        
        Before using this value, ensure that (a) the magnetometer
        has been calibrated and (b) that a magnetic disturbance is
        not taking place at the instant when the compass heading
        was generated.
        :returns: The current tilt-compensated compass heading, in degrees (0-360).
        """
        return self.compass_heading

    def zeroYaw(self):
        """Sets the user-specified yaw offset to the current
        yaw value reported by the sensor.
        
        This user-specified yaw offset is automatically
        subtracted from subsequent yaw values reported by
        the getYaw() method.
        """
        if self._isBoardYawResetSupported():
            self.io.zeroYaw()
            # Notification is deferred until action is complete.
        else:
            self.yaw_offset_tracker.setOffset()
            # Notification occurs immediately.
            self._yawResetComplete()
    
    def isCalibrating(self):
        """Returns true if the sensor is currently performing automatic
        gyro/accelerometer calibration.  Automatic calibration occurs
        when the sensor is initially powered on, during which time the
        sensor should be held still, with the Z-axis pointing up
        (perpendicular to the earth).
        
        .. note::  During this automatic calibration, the yaw, pitch and roll
                   values returned may not be accurate.
        
        Once calibration is complete, the sensor will automatically remove
        an internal yaw offset value from all reported values.
        
        :returns: Returns true if the sensor is currently automatically
                  calibrating the gyro and accelerometer sensors.
        """
        return (self.cal_status & \
                    AHRSProtocol.NAVX_CAL_STATUS_IMU_CAL_STATE_MASK) != \
                        AHRSProtocol.NAVX_CAL_STATUS_IMU_CAL_COMPLETE
                        
    def isConnected(self):
        """Indicates whether the sensor is currently connected
        to the host computer.  A connection is considered established
        whenever communication with the sensor has occurred recently.
        
        :returns: Returns true if a valid update has been recently received
                  from the sensor.
        """
        return self.io.isConnected()
    
    def getByteCount(self):
        """Returns the count in bytes of data received from the
        sensor. This could can be useful for diagnosing
        connectivity issues.
        
        If the byte count is increasing, but the update count
        (see :meth:`getUpdateCount`) is not, this indicates a software
        misconfiguration.
        
        :returns: The number of bytes received from the sensor.
        """
        return self.io.getByteCount()
    
    def getActualUpdateRate(self):
        """Returns the navX-Model device's currently configured update
        rate.  Note that the update rate that can actually be realized
        is a value evenly divisible by the navX-Model device's internal
        motion processor sample clock (200Hz).  Therefore, the rate that
        is returned may be lower than the requested sample rate.
        
        The actual sample rate is rounded down to the nearest integer
        that is divisible by the number of Digital Motion Processor clock
        ticks.  For instance, a request for 58 Hertz will result in
        an actual rate of 66Hz (200 / (200 / 58), using integer
        math.
        
        :returns: Returns the current actual update rate in Hz
        (cycles per second).
        """
        actual_update_rate = self._getActualUpdateRateInternal(self.getRequestedUpdateRate())
        return int(actual_update_rate & 0xFF)
    
    def _getActualUpdateRateInternal(self, update_rate):
        NAVX_MOTION_PROCESSOR_UPDATE_RATE_HZ = 200
        integer_update_rate = int(update_rate & 0xFF)
        realized_update_rate = NAVX_MOTION_PROCESSOR_UPDATE_RATE_HZ / \
                (NAVX_MOTION_PROCESSOR_UPDATE_RATE_HZ / integer_update_rate)
        return realized_update_rate
    
    def getRequestedUpdateRate(self):
        """Returns the currently requested update rate.
        rate.  Note that not every update rate can actually be realized,
        since the actual update rate must be a value evenly divisible by
        the navX-Model device's internal motion processor sample clock (200Hz).
        
        To determine the actual update rate, use the
        {@link #getActualUpdateRate()} method.
        
        :returns: Returns the requested update rate in Hz
        (cycles per second).
        """
        return int(self.update_rate_hz & 0xFF)
    
    def getUpdateCount(self):
        """Returns the count of valid updates which have
        been received from the sensor.  This count should increase
        at the same rate indicated by the configured update rate.
        
        :returns: The number of valid updates received from the sensor.
        """
       
        return self.io.getUpdateCount()
    
    def getLastSensorTimestamp(self):
        """Returns the sensor timestamp corresponding to the
        last sample retrieved from the sensor.  Note that this
        sensor timestamp is only provided when the Register-based
        IO methods (SPI, I2C) are used; sensor timestamps are not
        provided when Serial-based IO methods (TTL UART, USB)
        are used.
        
        :returns: The sensor timestamp (in ms) corresponding to the
                  current AHRS sensor data.
        :rtype: int
        """
        return self.last_sensor_timestamp
    
    def getWorldLinearAccelX(self):
        """Returns the current linear acceleration in the X-axis (in G).
        
        World linear acceleration refers to raw acceleration data, which
        has had the gravity component removed, and which has been rotated to
        the same reference frame as the current yaw value.  The resulting
        value represents the current acceleration in the x-axis of the
        body (e.g., the robot) on which the sensor is mounted.
        
        :returns: Current world linear acceleration in the X-axis (in G).
        """
        return self.world_linear_accel_x
    
    def getWorldLinearAccelY(self):
        """Returns the current linear acceleration in the Y-axis (in G).
        
        World linear acceleration refers to raw acceleration data, which
        has had the gravity component removed, and which has been rotated to
        the same reference frame as the current yaw value.  The resulting
        value represents the current acceleration in the Y-axis of the
        body (e.g., the robot) on which the sensor is mounted.
        
        :returns: Current world linear acceleration in the Y-axis (in G).
        """
        return self.world_linear_accel_y
    
    def getWorldLinearAccelZ(self):
        """Returns the current linear acceleration in the Z-axis (in G).
        
        World linear acceleration refers to raw acceleration data, which
        has had the gravity component removed, and which has been rotated to
        the same reference frame as the current yaw value.  The resulting
        value represents the current acceleration in the Z-axis of the
        body (e.g., the robot) on which the sensor is mounted.
        
        :returns: Current world linear acceleration in the Z-axis (in G).
        """
        return self.world_linear_accel_z
    
    def isMoving(self):
        """Indicates if the sensor is currently detecting motion,
        based upon the X and Y-axis world linear acceleration values.
        If the sum of the absolute values of the X and Y axis exceed
        a "motion threshold", the motion state is indicated.
        
        :returns: Returns true if the sensor is currently detecting motion.
        """
        return self.is_moving
    
    def isRotating(self):
        """Indicates if the sensor is currently detecting motion,
        based upon the X and Y-axis world linear acceleration values.
        If the sum of the absolute values of the X and Y axis exceed
        a "motion threshold", the motion state is indicated.
        
        :returns: Returns true if the sensor is currently detecting motion.
        """
        return self.is_rotating
    
    def getBarometricPressure(self):
        """Returns the current barometric pressure, based upon calibrated readings
        from the onboard pressure sensor.  This value is in units of millibar.
        
        .. note:: This value is only valid for a navX Aero.  To determine
                  whether this value is valid, see :meth:`isAltitudeValid`.
                  
        :returns: Returns current barometric pressure (navX Aero only).
        """
        return self.baro_pressure

    def getAltitude(self):
        """Returns the current altitude, based upon calibrated readings
        from a barometric pressure sensor, and the currently-configured
        sea-level barometric pressure [navX Aero only].  This value is in units of meters.
        
        .. note:: This value is only valid sensors including a pressure
                  sensor.  To determine whether this value is valid, see
                  :meth:`isAltitudeValid`.
        
        :returns: Returns current altitude in meters (as long as the sensor includes
                  an installed on-board pressure sensor).
        """
        return self.altitude
    
    def isAltitudeValid(self):
        """Indicates whether the current altitude (and barometric pressure) data is
        valid. This value will only be true for a sensor with an onboard
        pressure sensor installed.
        
        If this value is false for a board with an installed pressure sensor,
        this indicates a malfunction of the onboard pressure sensor.
        
        :returns: Returns true if a working pressure sensor is installed.
        """
        return self.altitude_valid
    
    def getFusedHeading(self):
        """Returns the "fused" (9-axis) heading.
        
        The 9-axis heading is the fusion of the yaw angle, the tilt-corrected
        compass heading, and magnetic disturbance detection.  Note that the
        magnetometer calibration procedure is required in order to
        achieve valid 9-axis headings.
        
        The 9-axis Heading represents the sensor's best estimate of current heading,
        based upon the last known valid Compass Angle, and updated by the change in the
        Yaw Angle since the last known valid Compass Angle.  The last known valid Compass
        Angle is updated whenever a Calibrated Compass Angle is read and the sensor
        has recently rotated less than the Compass Noise Bandwidth (~2 degrees).
        
        :returns: Fused Heading in Degrees (range 0-360)
        """
        return self.fused_heading
    
    def isMagneticDisturbance(self):
        """Indicates whether the current magnetic field strength diverges from the
        calibrated value for the earth's magnetic field by more than the currently-
        configured Magnetic Disturbance Ratio.
        
        This function will always return false if the sensor's magnetometer has
        not yet been calibrated (see :meth:`isMagnetometerCalibrated`).
        
        :returns: true if a magnetic disturbance is detected (or the magnetometer is uncalibrated).
        """
        return self.magnetic_disturbance
    
    def isMagnetometerCalibrated(self):
        """Indicates whether the magnetometer has been calibrated.
        
        Magnetometer Calibration must be performed by the user.
        
        Note that if this function does indicate the magnetometer is calibrated,
        this does not necessarily mean that the calibration quality is sufficient
        to yield valid compass headings.
        
        :returns: Returns true if magnetometer calibration has been performed.
        """
        return self.is_magnetometer_calibrated
    
    #
    # Unit Quaternions
    #
    
    def getQuaternionW(self):
        """Returns the imaginary portion (W) of the Orientation Quaternion which
        fully describes the current sensor orientation with respect to the
        reference angle defined as the angle at which the yaw was last "zeroed".
        
        Each quaternion value (W,X,Y,Z) is expressed as a value ranging from -2
        to 2.  This total range (4) can be associated with a unit circle, since
        each circle is comprised of 4 PI Radians.
        
        For more information on Quaternions and their use, please see this <a href=https://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation>definition</a>.
        
        :returns: Returns the imaginary portion (W) of the quaternion.
        """
        return self.quaternionW
    
    def getQuaternionX(self):
        """Returns the real portion (X axis) of the Orientation Quaternion which
        fully describes the current sensor orientation with respect to the
        reference angle defined as the angle at which the yaw was last "zeroed".
        
        Each quaternion value (W,X,Y,Z) is expressed as a value ranging from -2
        to 2.  This total range (4) can be associated with a unit circle, since
        each circle is comprised of 4 PI Radians.
        
        For more information on Quaternions and their use, please see this <a href=https://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation>description</a>.
        
        :returns: Returns the real portion (X) of the quaternion.
        """
        return self.quaternionX
    
    def getQuaternionY(self):
        """Returns the real portion (Y axis) of the Orientation Quaternion which
        fully describes the current sensor orientation with respect to the
        reference angle defined as the angle at which the yaw was last "zeroed".
        
        Each quaternion value (W,X,Y,Z) is expressed as a value ranging from -2
        to 2.  This total range (4) can be associated with a unit circle, since
        each circle is comprised of 4 PI Radians.
        
        For more information on Quaternions and their use, please see:
        
        https://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation
        
        :returns: Returns the real portion (X) of the quaternion.
        """
        return self.quaternionY
    
    def getQuaternionZ(self):
        """Returns the real portion (Z axis) of the Orientation Quaternion which
        fully describes the current sensor orientation with respect to the
        reference angle defined as the angle at which the yaw was last "zeroed".
        
        Each quaternion value (W,X,Y,Z) is expressed as a value ranging from -2
        to 2.  This total range (4) can be associated with a unit circle, since
        each circle is comprised of 4 PI Radians.
        
        For more information on Quaternions and their use, please see:
        
        https://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation
        
        :returns: Returns the real portion (X) of the quaternion.
        """
        return self.quaternionZ
    
    def resetDisplacement(self):
        """Zeros the displacement integration variables.   Invoke this at the moment when
        integration begins.
        """
        if self._isDisplacementSupported():
            self.io.zeroDisplacement()
        else:
            self.integrator.resetDisplacement()
    
    def _updateDisplacement(self, accel_x_g, accel_y_g, 
                            update_rate_hz, is_moving):
        """Each time new linear acceleration samples are received, this function should be invoked.
        This function transforms acceleration in G to meters/sec^2, then converts this value to
        Velocity in meters/sec (based upon velocity in the previous sample).  Finally, this value
        is converted to displacement in meters, and integrated.
        """
        self.integrator.updateDisplacement(accel_x_g, accel_y_g, update_rate_hz, is_moving)
    
    def getVelocityX(self):
        """Returns the velocity (in meters/sec) of the X axis [Experimental].
        
        .. note:: This feature is experimental.  Velocity measures rely on integration
                  of acceleration values from MEMS accelerometers which yield "noisy" values.  The
                  resulting velocities are not known to be very accurate.
                    
        :returns: Current Velocity (in meters/squared).
        """
        if self._isDisplacementSupported():
            return self.vel_x
        else:
            return self.integrator.getVelocityX()
    
    def getVelocityY(self):
        """Returns the velocity (in meters/sec) of the Y axis [Experimental].
        
        .. note:: This feature is experimental.  Velocity measures rely on integration
                  of acceleration values from MEMS accelerometers which yield "noisy" values.  The
                  resulting velocities are not known to be very accurate.
                    
        :returns: Current Velocity (in meters/squared).
        """
        if self._isDisplacementSupported():
            return self.vel_y
        else:
            return self.integrator.getVelocityY()
    
    def getVelocityZ(self):
        """Returns the velocity (in meters/sec) of the X axis [Experimental].
        
        .. note:: This feature is experimental.  Velocity measures rely on integration
                  of acceleration values from MEMS accelerometers which yield "noisy" values.  The
                  resulting velocities are not known to be very accurate.
                    
        :returns: Current Velocity (in meters/squared).
        """
        if self._isDisplacementSupported():
            return self.vel_z
        else:
            return self.integrator.getVelocityZ()
    

    
    def getDisplacementX(self):
        """Returns the displacement (in meters) of the X axis since resetDisplacement()
        was last invoked [Experimental].
        
        .. note:: This feature is experimental.  Displacement measures rely on double-integration
                  of acceleration values from MEMS accelerometers which yield "noisy" values.  The
                  resulting displacement are not known to be very accurate, and the amount of error
                  increases quickly as time progresses.
                  
        :returns: Displacement since last reset (in meters).
        """
        if self._isDisplacementSupported():
            return self.disp_x
        else:
            return self.integrator.getDisplacementX()
        
    
    
    def getDisplacementY(self):
        """Returns the displacement (in meters) of the Y axis since resetDisplacement()
        was last invoked [Experimental].
        
        .. note:: This feature is experimental.  Displacement measures rely on double-integration
                  of acceleration values from MEMS accelerometers which yield "noisy" values.  The
                  resulting displacement are not known to be very accurate, and the amount of error
                  increases quickly as time progresses.
                  
        :returns: Displacement since last reset (in meters).
        """
        if self._isDisplacementSupported():
            return self.disp_y
        else:
            return self.integrator.getDisplacementY()
        
    def getDisplacementZ(self):
        """Returns the displacement (in meters) of the Z axis since resetDisplacement()
        was last invoked [Experimental].
        
        .. note:: This feature is experimental.  Displacement measures rely on double-integration
                  of acceleration values from MEMS accelerometers which yield "noisy" values.  The
                  resulting displacement are not known to be very accurate, and the amount of error
                  increases quickly as time progresses.
                  
        :returns: Displacement since last reset (in meters).
        """
        if self._isDisplacementSupported():
            return self.disp_z
        else:
            return self.integrator.getDisplacementZ()
    
    def registerCallback(self, callback):
        """Registers a callback interface.  This interface
        will be called back when new data is available,
        based upon a change in the sensor timestamp.
        
        Note that this callback will occur within the context of the
        device IO thread, which is not the same thread context the
        caller typically executes in.
        """
        self.callbacks.append(callback)
        return True

    def deregisterCallback(self, callback):
        """Deregisters a previously registered callback interface.
        
        Be sure to deregister any callback which have been
        previously registered, to ensure that the object
        implementing the callback interface does not continue
        to be accessed when no longer necessary.
        """
        try:
            self.callbacks.remove(callback)
            return True
        except ValueError:
            return False
    
    #**********************************************************
    # PIDSource Interface Implementation
    #**********************************************************
    
    
    def pidGet(self):
        """Returns the current value to use for PID, based on the PIDSourceType.
        
        If the PIDSourceType is kDisplacement, this returns the Yaw Angle
        in degrees (-180 to 180). See :meth:`getYaw`.
        
        If the PIDSourceType is kRate, this returns the rate of rotation in
        degrees per seconds. See :meth:`getRate`.
        
        :returns: The current yaw angle or rate.
        """
        if self.pidSource == self.PIDSourceType.kDisplacement:
            return self.getYaw()
        elif self.pidSource == self.PIDSourceType.kRate:
            return self.getRate()
        else:
            return 0.0
    
    def setPIDSourceType(self, pidSource):
        self.pidSource = pidSource
    
    def getPIDSourceType(self):
        return self.pidSource
    
    def getAngle(self):
        """Returns the total accumulated yaw angle (Z Axis, in degrees)
        reported by the sensor.
        
        .. note:: The angle is continuous, meaning it's range is beyond 360 degrees.
                  This ensures that algorithms that wouldn't want to see a discontinuity
                  in the gyro output as it sweeps past 0 on the second time around.
        
        Note that the returned yaw value will be offset by a user-specified
        offset value this user-specified offset value is set by
        invoking the zeroYaw() method.
        
        :returns: The current total accumulated yaw angle (Z axis) of the robot
                  in degrees. This heading is based on integration of the returned rate
                  from the Z-axis (yaw) gyro.
        """
        return self.yaw_angle_tracker.getAngle()
    
    def getRate(self):
        """Return the rate of rotation of the yaw (Z-axis) gyro, in degrees per second.
        
        The rate is based on the most recent reading of the yaw gyro angle.
        
        :returns: The current rate of change in yaw angle (in degrees per second)
        """
        return self.yaw_angle_tracker.getRate()
    
    def setAngleAdjustment(self, adjustment):
        """Sets an amount of angle to be automatically added before returning a
        angle from the :meth:`getAngle` method.  This allows users of the ``getAngle`` method
        to logically rotate the sensor by a given amount of degrees.
        
        NOTE 1:  The adjustment angle is **only** applied to the value returned
        from ``getAngle`` - it does not adjust the value returned from :meth:`getYaw`, nor
        any of the quaternion values.
        
        NOTE 2:  The adjustment angle is **not** automatically cleared whenever the
        sensor yaw angle is reset.
        
        If not set, the default adjustment angle is 0 degrees (no adjustment).
        
        :param adjustment: in degrees (range:  -360 to 360)
        """
        self.yaw_angle_tracker.setAngleAdjustment(adjustment)
    
    def getAngleAdjustment(self):
        """Returns the currently configured adjustment angle.  See
        :meth:`setAngleAdjustment` for more details.
        
        If this method returns 0 degrees, no adjustment to the value returned
        via :meth:`getAngle` will occur.
        :returns: adjustment, in degrees (range:  -360 to 360)
        """
        return self.yaw_angle_tracker.getAngleAdjustment()
    
    def reset(self):
        """Reset the Yaw gyro.
        
        Resets the Gyro Z (Yaw) axis to a heading of zero. This can be used if
        there is significant drift in the gyro and it needs to be recalibrated
        after it has been running.
        """
        self.zeroYaw()
    
    def getRawGyroX(self):
        """Returns the current raw (unprocessed) X-axis gyro rotation rate (in degrees/sec).
        
        .. note:: This value is un-processed, and should only be accessed by advanced users.
                    Typically, rotation about the X Axis is referred to as "Pitch".  Calibrated
                    and Integrated Pitch data is accessible via the :meth:`getPitch` method.
        
        :returns: Returns the current rotation rate (in degrees/sec).
        """
        return self.raw_gyro_x / (DEV_UNITS_MAX / self.gyro_fsr_dps)
    
    def getRawGyroY(self):
        """Returns the current raw (unprocessed) Y-axis gyro rotation rate (in degrees/sec).
        
        .. note:: This value is un-processed, and should only be accessed by advanced users.
                    Typically, rotation about the T Axis is referred to as "Roll".  Calibrated
                    and Integrated Pitch data is accessible via the :meth:`getRoll` method.
        
        :returns: Returns the current rotation rate (in degrees/sec).
        """
        return self.raw_gyro_y / (DEV_UNITS_MAX / self.gyro_fsr_dps)
    
    def getRawGyroZ(self):
        """Returns the current raw (unprocessed) Z-axis gyro rotation rate (in degrees/sec).
        
        .. note:: This value is un-processed, and should only be accessed by advanced users.
                  Typically, rotation about the T Axis is referred to as "Yaw".  Calibrated
                  and Integrated Pitch data is accessible via the :meth:`getYaw` method.
        
        :returns: Returns the current rotation rate (in degrees/sec).
        """
        return self.raw_gyro_z / (DEV_UNITS_MAX / self.gyro_fsr_dps)
    
    def getRawAccelX(self):
        """Returns the current raw (unprocessed) X-axis acceleration rate (in G).
        
        .. note:: this value is unprocessed, and should only be accessed by advanced users.  This raw value
                  has not had acceleration due to gravity removed from it, and has not been rotated to
                  the world reference frame.  Gravity-corrected, world reference frame-corrected
                  X axis acceleration data is accessible via the :meth:`getWorldLinearAccelX` method.
        
        :returns: Returns the current acceleration rate (in G).
        """
        return self.raw_accel_x / (DEV_UNITS_MAX / self.accel_fsr_g)

    def getRawAccelY(self):
        """Returns the current raw (unprocessed) Y-axis acceleration rate (in G).
        
        .. note:: this value is unprocessed, and should only be accessed by advanced users.  This raw value
                  has not had acceleration due to gravity removed from it, and has not been rotated to
                  the world reference frame.  Gravity-corrected, world reference frame-corrected
                  Y axis acceleration data is accessible via the :meth:`getWorldLinearAccelY` method.
        
        :returns: Returns the current acceleration rate (in G).
        """
        return self.raw_accel_y / (DEV_UNITS_MAX / self.accel_fsr_g)
    
    def getRawAccelZ(self):
        """Returns the current raw (unprocessed) Z-axis acceleration rate (in G).
        
        .. note:: this value is unprocessed, and should only be accessed by advanced users.  This raw value
                  has not had acceleration due to gravity removed from it, and has not been rotated to
                  the world reference frame.  Gravity-corrected, world reference frame-corrected
                  Z axis acceleration data is accessible via the :meth:`getWorldLinearAccelZ` method.
        
        :returns: Returns the current acceleration rate (in G).
        """
        return self.raw_accel_z / (DEV_UNITS_MAX / self.accel_fsr_g)
    
    
    def getRawMagX(self):
        """Returns the current raw (unprocessed) X-axis magnetometer reading (in uTesla).
        
        .. note::  this value is unprocessed, and should only be accessed by advanced users.  This raw value
                    has not been tilt-corrected, and has not been combined with the other magnetometer axis
                    data to yield a compass heading.  Tilt-corrected compass heading data is accessible
                    via the :meth:`getCompassHeading` method.
        
        :returns: Returns the mag field strength (in uTesla).
        """
        return self.cal_mag_x / UTESLA_PER_DEV_UNIT

    def getRawMagY(self):
        """Returns the current raw (unprocessed) Y-axis magnetometer reading (in uTesla).
        
        .. note::  this value is unprocessed, and should only be accessed by advanced users.  This raw value
                    has not been tilt-corrected, and has not been combined with the other magnetometer axis
                    data to yield a compass heading.  Tilt-corrected compass heading data is accessible
                    via the :meth:`getCompassHeading` method.
        
        :returns: Returns the mag field strength (in uTesla).
        """
        return self.cal_mag_y / UTESLA_PER_DEV_UNIT
    
    def getRawMagZ(self):
        """Returns the current raw (unprocessed) Z-axis magnetometer reading (in uTesla).
        
        .. note::  this value is unprocessed, and should only be accessed by advanced users.  This raw value
                    has not been tilt-corrected, and has not been combined with the other magnetometer axis
                    data to yield a compass heading.  Tilt-corrected compass heading data is accessible
                    via the :meth:`getCompassHeading` method.
        
        :returns: Returns the mag field strength (in uTesla).
        """
        return self.cal_mag_z / UTESLA_PER_DEV_UNIT
     
    def getPressure(self):
        """Returns the current barometric pressure (in millibar) [navX Aero only].
        
        This value is valid only if a barometric pressure sensor is onboard.
        
        :returns: Returns the current barometric pressure (in millibar).
        """
        # TODO implement for navX-Aero.
        return 0
    
    def getTempC(self):
        """Returns the current temperature (in degrees centigrade) reported by
        the sensor's gyro/accelerometer circuit.
        
        This value may be useful in order to perform advanced temperature-
        correction of raw gyroscope and accelerometer values.
        
        :returns: The current temperature (in degrees centigrade).
        """
        return self.mpu_temp_c
    
    def getBoardYawAxis(self):
        """Returns information regarding which sensor board axis (X,Y or Z) and
        direction (up/down) is currently configured to report Yaw (Z) angle
        values.   NOTE:  If the board firmware supports Omnimount, the board yaw
        axis/direction are configurable.
        
        For more information on Omnimount, please see:
        
        http://navx-mxp.kauailabs.com/navx-mxp/installation/omnimount/
        
        :returns: The currently-configured board yaw axis/direction as a
                  tuple of (up, axis). Up can be True/False, axis is 'x', 'y', or 'z')
        """
        yaw_axis_info = self.capability_flags >> 3
        yaw_axis_info &= 7
        if yaw_axis_info == AHRSProtocol.OMNIMOUNT_DEFAULT:
            up = True
            yaw_axis = 'z'
        else:
            up = True if yaw_axis_info & 0x01 != 0 else False
            yaw_axis_info >>= 1
            if yaw_axis_info == 0:
                yaw_axis = 'x'
            elif yaw_axis_info == 1:
                yaw_axis = 'y'
            elif yaw_axis_info == 2:
                yaw_axis = 'z'
            
        return up, yaw_axis

    def getFirmwareVersion(self):
        """Returns the version number of the firmware currently executing
        on the sensor.
        
        To update the firmware to the latest version, please see:
        
        http://navx-mxp.kauailabs.com/navx-mxp/support/updating-firmware/
        
        :returns: The firmware version in the format [MajorVersion].[MinorVersion]
        """
        return '%s.%s' % (self.fw_ver_major, self.fw_ver_minor)
    
    #
    # Internal API
    #
    
    def _isOmniMountSupported(self):
        return (self.capability_flags & AHRSProtocol.NAVX_CAPABILITY_FLAG_OMNIMOUNT) != 0
    
    def _isBoardYawResetSupported(self):
        return (self.capability_flags & AHRSProtocol.NAVX_CAPABILITY_FLAG_YAW_RESET) != 0
    
    def _isDisplacementSupported(self):
        return (self.capability_flags & AHRSProtocol.NAVX_CAPABILITY_FLAG_VEL_AND_DISP) != 0
    
    def _isAHRSPosTimestampSupported(self):
        return (self.capability_flags & AHRSProtocol.NAVX_CAPABILITY_FLAG_AHRSPOS_TS) != 0
    
    # iocomplete notification stuff
    
    def _setYawPitchRoll(self, o, sensor_timestamp):
        with self.mutex:
            self.__dict__.update(o.__dict__)
            self.last_sensor_timestamp = sensor_timestamp
    
    def _setAHRSPosData(self, o, sensor_timestamp):
        with self.mutex:
            self.__dict__.update(o.__dict__)
            self.last_sensor_timestamp = sensor_timestamp
            
            self.yaw_offset_tracker.updateHistory(self.yaw)
            self.yaw_angle_tracker.nextAngle(self.getYaw())
            
            callbacks = self.callbacks[:]
            
        for callback in callbacks:
            callback(o, sensor_timestamp)
    
    def _setRawData(self, o, sensor_timestamp):
        with self.mutex:
            self.__dict__.update(o.__dict__)
            self.last_sensor_timestamp = sensor_timestamp
    
    def _setAHRSData(self, o, sensor_timestamp):
        with self.mutex:
            self.__dict__.update(o.__dict__)
            self.last_sensor_timestamp = sensor_timestamp
            
            self.yaw_offset_tracker.updateHistory(self.yaw)
            
            self._updateDisplacement(o.world_linear_accel_x,
                                     o.world_linear_accel_y,
                                     self.update_rate_hz,
                                     self.is_moving)
            
            self.yaw_angle_tracker.nextAngle(self.getYaw())
            
            callbacks = self.callbacks[:]
            
        for callback in callbacks:
            callback(o, sensor_timestamp)
    
    def _setBoardID(self, o):
        with self.mutex:
            self.__dict__.update(o.__dict__)
    
    def _setBoardState(self, o):
        with self.mutex:
            self.__dict__.update(o.__dict__)
            
    def _yawResetComplete(self):
        self.yaw_angle_tracker.reset()
    
    #
    # LiveWindow 
    #
    
    def getSmartDashboardType(self):
        return "Gyro"
    
    def updateTable(self):
        table = self.getTable()
        if table is not None:
            table.putNumber("Value", self.getYaw())
        
