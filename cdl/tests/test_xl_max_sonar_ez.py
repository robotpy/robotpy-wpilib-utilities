from .. import xl_max_sonar_ez


def test_digital_sensor():
    digital = xl_max_sonar_ez.MaxSonarEZPulseWidth(1)
    assert digital.get() == 0


def test_analog_sensor():
    analog = xl_max_sonar_ez.MaxSonarEZAnalog(1)
    assert analog.get() == 0
