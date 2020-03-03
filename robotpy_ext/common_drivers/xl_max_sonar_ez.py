"""
These are a set of drivers for the XL-MaxSonar EZ series of sonar modules.
The devices have a few different ways of reading from them, and the these drivers attempt to cover
some of the methods
"""
import wpilib

from . import driver_base
from . import units


class MaxSonarEZPulseWidth(driver_base.DriverBase):
    """
    This is a driver for the MaxSonar EZ series of sonar sensors, using the pulse-width output of the sensor.

    To use this driver, pin 2 on the sensor must be mapped to a dio pin.
    """

    verified = True

    def __init__(self, channel, output_units=units.inch):
        """Sonar sensor constructor

        :param channel: The digital input index which is wired to the pulse-width output pin (pin 2) on the sensor.
        :param output_units: The Unit instance specifying the format of value to return
        """

        # Save value
        self.output_units = output_units

        # Setup the counter
        self.counter = wpilib.Counter(channel)
        self.counter.setSemiPeriodMode(highSemiPeriod=True)

        # Call the parents
        super().__init__()

    def get(self):
        """Return the current sonar sensor reading, in the units specified from the constructor"""
        inches = self.counter.getPeriod() / 0.000147
        return units.convert(units.inch, self.output_units, inches)


class MaxSonarEZAnalog(driver_base.DriverBase):
    """
    This is a driver for the MaxSonar EZ series of sonar sensors, using the analog output of the sensor.

    To use this driver, pin 3 on the sensor must be mapped to an analog pin, and the sensor must be on a 5v supply.
    """

    # This code has actually never been run, so it is extra not-verified!
    verified = False

    def __init__(self, channel, output_units=units.inch):
        """Sonar sensor constructor

        :param channel: The analog input index which is wired to the analog output pin (pin 3) on the sensor.
        :param output_units: The Unit instance specifying the format of value to return
        """

        # Save value
        self.output_units = output_units

        # Setup the analog input
        self.analog = wpilib.AnalogInput(channel)

        # Call the parents
        super().__init__()

    def get(self):
        """Return the current sonar sensor reading, in the units specified from the constructor"""
        centimeters = self.analog.getVoltage() / 0.0049
        return units.convert(units.centimeter, self.output_units, centimeters)
