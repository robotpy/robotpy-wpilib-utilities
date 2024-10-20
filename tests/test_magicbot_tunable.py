from typing import ClassVar, List, Sequence

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
        assert getattr(component, name) == value

    for name, value in [
        ("rotation", geometry.Rotation2d()),
    ]:
        struct_type = type(value)
        assert nt.getTopic(name).getTypeString() == f"struct:{struct_type.__name__}"
        topic = nt.getStructTopic(name, struct_type)
        assert topic.subscribe(None).get() == value
        assert getattr(component, name) == value

    for name, struct_type, value in [
        ("rotations", geometry.Rotation2d, [geometry.Rotation2d()]),
    ]:
        assert nt.getTopic(name).getTypeString() == f"struct:{struct_type.__name__}[]"
        topic = nt.getStructArrayTopic(name, struct_type)
        assert topic.subscribe([]).get() == value
        assert getattr(component, name) == value


def test_tunable_errors():
    with pytest.raises(TypeError):

        class Component:
            invalid = tunable(None)


def test_tunable_errors_with_empty_sequence():
    with pytest.raises((RuntimeError, ValueError)):

        class Component:
            empty = tunable([])


def test_type_hinted_empty_sequences() -> None:
    class Component:
        generic_seq = tunable[Sequence[int]](())
        class_var_seq: ClassVar[tunable[Sequence[int]]] = tunable(())
        inst_seq: Sequence[int] = tunable(())

        generic_typing_list = tunable[List[int]]([])
        class_var_typing_list: ClassVar[tunable[List[int]]] = tunable([])
        inst_typing_list: List[int] = tunable([])

        generic_list = tunable[list[int]]([])
        class_var_list: ClassVar[tunable[list[int]]] = tunable([])
        inst_list: list[int] = tunable([])

    component = Component()
    setup_tunables(component, "test_type_hinted_sequences")
    NetworkTables = ntcore.NetworkTableInstance.getDefault()
    nt = NetworkTables.getTable("/components/test_type_hinted_sequences")

    for name in [
        "generic_seq",
        "class_var_seq",
        "inst_seq",
        "generic_typing_list",
        "class_var_typing_list",
        "inst_typing_list",
        "generic_list",
        "class_var_list",
        "inst_list",
    ]:
        assert nt.getTopic(name).getTypeString() == "int[]"
        entry = nt.getEntry(name)
        assert entry.getIntegerArray(None) == []
        assert getattr(component, name) == []
