from robotpy_ext.common_drivers.distance_sensors import (
    SharpIR2Y0A02,
    SharpIR2Y0A21,
    SharpIR2Y0A41,
)

from robotpy_ext.common_drivers.distance_sensors_sim import (
    SharpIR2Y0A02Sim,
    SharpIR2Y0A21Sim,
    SharpIR2Y0A41Sim,
)

import pytest


def test_2Y0A02(hal):
    sensor = SharpIR2Y0A02(0)
    sim = SharpIR2Y0A02Sim(sensor)

    # 22 to 145cm

    # min
    sim.setDistance(10)
    assert sensor.getDistance() == pytest.approx(22.5)

    # max
    sim.setDistance(200)
    assert sensor.getDistance() == pytest.approx(145)

    # middle
    sim.setDistance(50)
    assert sensor.getDistance() == pytest.approx(50)

    sim.setDistance(100)
    assert sensor.getDistance() == pytest.approx(100)


def test_2Y0A021(hal):
    sensor = SharpIR2Y0A21(0)
    sim = SharpIR2Y0A21Sim(sensor)

    # 10 to 80cm

    # min
    sim.setDistance(5)
    assert sensor.getDistance() == pytest.approx(10)

    # max
    sim.setDistance(100)
    assert sensor.getDistance() == pytest.approx(80)

    # middle
    sim.setDistance(30)
    assert sensor.getDistance() == pytest.approx(30)

    sim.setDistance(60)
    assert sensor.getDistance() == pytest.approx(60)


def test_2Y0A041(hal):
    sensor = SharpIR2Y0A41(0)
    sim = SharpIR2Y0A41Sim(sensor)

    # 4.5 to 35 cm

    # min
    sim.setDistance(2)
    assert sensor.getDistance() == pytest.approx(4.5)

    # max
    sim.setDistance(50)
    assert sensor.getDistance() == pytest.approx(35)

    # middle
    sim.setDistance(10)
    assert sensor.getDistance() == pytest.approx(10)

    sim.setDistance(25)
    assert sensor.getDistance() == pytest.approx(25)
