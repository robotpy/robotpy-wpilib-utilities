from robotpy_ext.common_drivers import units


def close_enough(val_1, val_2):
    """Quick function to determine if val_1 ~= val_2"""
    return abs(val_1 - val_2) < 0.001


def test_meters_to_cm():
    assert units.convert(units.meter, units.centimeter, 1) == 100
    assert units.convert(units.meter, units.centimeter, 50) == 5000


def test_cm_to_meters():
    assert units.convert(units.centimeter, units.meter, 100) == 1
    assert units.convert(units.centimeter, units.meter, 500) == 5


def test_feet_to_inches():
    assert close_enough(units.convert(units.foot, units.inch, 1), 12)
    assert close_enough(units.convert(units.foot, units.inch, 4), 48)


def test_inches_to_feet():
    assert close_enough(units.convert(units.inch, units.foot, 12), 1)
    assert close_enough(units.convert(units.inch, units.foot, 48), 4)


def test_feet_to_cm():
    assert close_enough(units.convert(units.foot, units.centimeter, 1), 30.48)
    assert close_enough(units.convert(units.foot, units.centimeter, 3), 91.44)


def test_cm_to_feet():
    assert close_enough(units.convert(units.centimeter, units.foot, 30.48), 1)
    assert close_enough(units.convert(units.centimeter, units.foot, 91.44), 3)
