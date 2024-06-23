from typing import Sequence

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
    def get_int(self) -> int:
        return 0

    @magicbot.feedback
    def get_float(self) -> float:
        return 0.5

    @magicbot.feedback
    def get_ints(self) -> Sequence[int]:
        return (0,)

    def execute(self):
        pass


class Robot(magicbot.MagicRobot):
    basic: BasicComponent
    type_hinted: TypeHintedComponent

    def createObjects(self):
        pass


def test_collect_feedbacks_with_type_hints():
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
        ("type_hinted/ints", "int[]", [0]),
    ):
        topic = nt.getTopic(name)
        assert topic.getTypeString() == type_str
        assert topic.genericSubscribe().get().value() == value
