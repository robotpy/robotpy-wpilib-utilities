def test_digital_sensor(wpimock):

    wpimock.Counter().getPeriod.return_value = 1 * 0.000147

    from robotpy_ext.common_drivers import xl_max_sonar_ez

    digital = xl_max_sonar_ez.MaxSonarEZPulseWidth(1)
    assert digital.get() == 1


def test_analog_sensor(wpimock):

    from robotpy_ext.common_drivers import xl_max_sonar_ez

    analog = xl_max_sonar_ez.MaxSonarEZAnalog(1)
    analog.analog.getVoltage.return_value = 1 * 0.0049 * 2.54

    assert analog.get() == 1
