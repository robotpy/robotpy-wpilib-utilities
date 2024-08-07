import ntcore
import pytest
from wpimath import geometry

from magicbot.magic_tunable import setup_tunables, tunable


def test_tunable() -> None:
    class Component:
        an_int = tunable(1)
        ints = tunable([0])
        floats = tunable([1.0, 2.0])
        rotation = tunable(geometry.Rotation2d())
        rotations = tunable([geometry.Rotation2d()])

    component = Component()
    setup_tunables(component, "test_tunable")
    nt = ntcore.NetworkTableInstance.getDefault().getTable("/components/test_tunable")

    for name, type_str, value in [
        ("an_int", "int", 1),
        ("ints", "int[]", [0]),
        ("floats", "double[]", [1.0, 2.0]),
    ]:
        topic = nt.getTopic(name)
        assert topic.getTypeString() == type_str
        assert topic.genericSubscribe().get().value() == value

    for name, value in [
        ("rotation", geometry.Rotation2d()),
    ]:
        struct_type = type(value)
        assert nt.getTopic(name).getTypeString() == f"struct:{struct_type.__name__}"
        topic = nt.getStructTopic(name, struct_type)
        assert topic.subscribe(None).get() == value

    for name, struct_type, value in [
        ("rotations", geometry.Rotation2d, [geometry.Rotation2d()]),
    ]:
        assert nt.getTopic(name).getTypeString() == f"struct:{struct_type.__name__}[]"
        topic = nt.getStructArrayTopic(name, struct_type)
        assert topic.subscribe([]).get() == value


def test_tunable_errors():
    with pytest.raises(TypeError):

        class Component:
            invalid = tunable(None)


def test_tunable_errors_with_empty_sequence():
    with pytest.raises(ValueError):

        class Component:
            empty = tunable([])
