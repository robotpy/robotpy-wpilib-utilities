def test_sensor(wpimock):
    from robotpy_ext.common_drivers.pressure_sensors import REVAnalogPressureSensor

    sensor = REVAnalogPressureSensor(3, 3.3)
    sensor.sensor.getAverageVoltage.return_value = 2.0
    assert int(sensor.pressure) == 126


def test_calibration(wpimock):
    from robotpy_ext.common_drivers.pressure_sensors import REVAnalogPressureSensor

    sensor = REVAnalogPressureSensor(3, 3.3)
    sensor.sensor.getAverageVoltage.return_value = 2.0
    sensor.calibrate(50)
    assert int(sensor.pressure) == 50
