import math
import wpilib

from wpilib.simulation import AnalogInputSim

from .distance_sensors import SharpIR2Y0A02, SharpIR2Y0A21, SharpIR2Y0A41


class SharpIR2Y0A02Sim:
    """
    An easy to use simulation interface for a Sharp GP2Y0A02YK0F
    """

    def __init__(self, sensor: SharpIR2Y0A02) -> None:
        assert isinstance(sensor, SharpIR2Y0A02)
        self._sim = AnalogInputSim(sensor.distance)
        self._distance = 0

    def getDistance(self) -> float:
        """Get set distance (not distance sensor sees) in centimeters"""
        return self._distance

    def setDistance(self, d) -> None:
        """Set distance in centimeters"""
        self._distance = d
        d = max(min(d, 145.0), 22.5)
        v = math.pow(d / 62.28, 1 / -1.092)
        self._sim.setVoltage(v)


class SharpIR2Y0A21Sim:
    """
    An easy to use simulation interface for a Sharp GP2Y0A21YK0F
    """

    def __init__(self, sensor: SharpIR2Y0A21) -> None:
        assert isinstance(sensor, SharpIR2Y0A21)
        self._sim = AnalogInputSim(sensor.distance)
        self._distance = 0

    def getDistance(self) -> float:
        """Get set distance (not distance sensor sees) in centimeters"""
        return self._distance

    def setDistance(self, d) -> None:
        """Set distance in centimeters"""
        self._distance = d
        d = max(min(d, 80.0), 10.0)
        v = math.pow(d / 26.449, 1 / -1.226)
        self._sim.setVoltage(v)


class SharpIR2Y0A41Sim:
    """
    An easy to use simulation interface for a Sharp GP2Y0A41SK0F
    """

    def __init__(self, sensor: SharpIR2Y0A41) -> None:
        assert isinstance(sensor, SharpIR2Y0A41)
        self._sim = AnalogInputSim(sensor.distance)
        self._distance = 0

    def getDistance(self) -> float:
        """Get set distance (not distance sensor sees) in centimeters"""
        return self._distance

    def setDistance(self, d) -> None:
        """Set distance in centimeters"""
        self._distance = d
        d = max(min(d, 35.0), 4.5)
        v = math.pow(d / 12.84, 1 / -0.9824)
        self._sim.setVoltage(v)
