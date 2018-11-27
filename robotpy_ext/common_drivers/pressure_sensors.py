from wpilib import AnalogInput


class REVAnalogPressureSensor:
    """
    The REV Robotics Analog Pressure Sensor is a 5V sensor
    that can measure pressures up to 200 PSI. It outputs an
    analog voltage that is proportional to the measured pressure.

    Pressure is derived from the following equation, taken from
    the data sheet::

        Pressure = 250 * (Vout / Vcc) -25

    where Vout is the output voltage of the sensor, and Vcc is the input
    voltage

    To calibrate the sensor, supply the sensor with a known
    pressure and call the calibrate method with the given
    pressure as the parameter
    """

    def __init__(self, channel, voltage_in=5):
        """
        :param voltage_in: Supply voltage to sensor from roboRIO
        """

        self.sensor = AnalogInput(channel)
        self.voltage_in = voltage_in

    @property
    def pressure(self):
        try:
            v = max(self.sensor.getAverageVoltage(), 0.00001)
            return (250 * (v / getattr(self, "Vn", self.voltage_in))) - 25
        except ZeroDivisionError:
            return 0

    def calibrate(self, known_pressure):
        """
        Calibrate calculated pressure to known pressure

        :param known_pressure: Known current pressure to calibrate to
        """

        Vo = max(self.sensor.getAverageVoltage(), 0.00001)
        self.Vn = Vo / (0.004 * known_pressure + 0.1)
