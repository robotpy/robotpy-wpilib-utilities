from typing import Sequence, Tuple

import ntcore
from wpimath import geometry

import magicbot


class BasicComponent:
    @magicbot.feedback
    def get_number(self):
        return 0

    @magicbot.feedback
    def get_ints(self):
        return (0,)

    @magicbot.feedback
    def get_floats(self):
        return (0.0, 0)

    def execute(self):
        pass


class TypeHintedComponent:
    @magicbot.feedback
    def get_rotation(self) -> geometry.Rotation2d:
        return geometry.Rotation2d()

    @magicbot.feedback
    def get_rotation_array(self) -> Sequence[geometry.Rotation2d]:
        return [geometry.Rotation2d()]

    @magicbot.feedback
    def get_rotation_2_tuple(self) -> Tuple[geometry.Rotation2d, geometry.Rotation2d]:
        return (geometry.Rotation2d(), geometry.Rotation2d())

    @magicbot.feedback
    def get_int(self) -> int:
        return 0

    @magicbot.feedback(properties={"unit": "seconds"})
    def get_float(self) -> float:
        return 0.5

    @magicbot.feedback.with_properties(units="meters")
    def get_distance(self) -> float:
        return 1.5

    @magicbot.feedback(key="velocity").with_properties(unit="m/s")
    def get_vel(self) -> float:
        return 3.0

    @magicbot.feedback
    def get_ints(self) -> Sequence[int]:
        return (0,)

    @magicbot.feedback
    def get_empty_strings(self) -> Sequence[str]:
        return ()

    def execute(self):
        pass


class Robot(magicbot.MagicRobot):
    basic: BasicComponent
    type_hinted: TypeHintedComponent

    def createObjects(self):
        pass


def test_feedbacks_with_type_hints():
    robot = Robot()
    robot.robotInit()
    nt = ntcore.NetworkTableInstance.getDefault().getTable("components")

    robot._do_periodics()

    for name, type_str, value in (
        ("basic/number", "double", 0.0),
        ("basic/ints", "int[]", [0]),
        ("basic/floats", "double[]", [0.0, 0.0]),
        ("type_hinted/int", "int", 0),
        ("type_hinted/float", "double", 0.5),
        ("type_hinted/distance", "double", 1.5),
        ("type_hinted/velocity", "double", 3.0),
        ("type_hinted/ints", "int[]", [0]),
        ("type_hinted/empty_strings", "string[]", []),
    ):
        topic = nt.getTopic(name)
        assert topic.getTypeString() == type_str
        assert topic.genericSubscribe().get().value() == value

    assert nt.getTopic("type_hinted/float").getProperty("unit") == "seconds"
    assert nt.getTopic("type_hinted/distance").getProperty("units") == "meters"
    assert nt.getTopic("type_hinted/velocity").getProperty("unit") == "m/s"

    for name, value in [
        ("type_hinted/rotation", geometry.Rotation2d()),
    ]:
        struct_type = type(value)
        assert nt.getTopic(name).getTypeString() == f"struct:{struct_type.__name__}"
        topic = nt.getStructTopic(name, struct_type)
        assert topic.subscribe(None).get() == value

    for name, struct_type, value in (
        ("type_hinted/rotation_array", geometry.Rotation2d, [geometry.Rotation2d()]),
        (
            "type_hinted/rotation_2_tuple",
            geometry.Rotation2d,
            [geometry.Rotation2d(), geometry.Rotation2d()],
        ),
    ):
        assert nt.getTopic(name).getTypeString() == f"struct:{struct_type.__name__}[]"
        topic = nt.getStructArrayTopic(name, struct_type)
        assert topic.subscribe([]).get() == value
