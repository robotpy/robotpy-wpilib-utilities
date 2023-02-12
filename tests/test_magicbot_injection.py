from typing import List, Tuple, Type, TypeVar
from unittest.mock import Mock

import magicbot


class Injectable:
    def __init__(self, num):
        self.num = num


class DumbComponent:
    def execute(self):
        pass


class Component1:
    intvar: int
    tupvar: tuple

    injectable: Injectable

    def execute(self):
        pass


class Component2:
    tupvar: tuple

    component1: Component1

    def execute(self):
        pass


class Component3:
    intvar: int

    def __init__(
        self,
        tupvar: Tuple[int, int],
        injectable: Injectable,
        component2: Component2,
    ) -> None:
        self.tuple_ = tupvar
        self.injectable_ = injectable
        self.component_2 = component2

    def execute(self):
        pass


class SimpleBot(magicbot.MagicRobot):
    intvar = 1
    tupvar = 1, 2

    component1: Component1
    component2: Component2
    component3: Component3

    def createObjects(self):
        self.injectable = Injectable(42)


class DuplicateComponent:
    var: tuple
    injectable: Injectable

    def execute(self):
        pass


class MultilevelBot(magicbot.MagicRobot):
    dup1: DuplicateComponent
    dup1_var = 1, 2

    dup2: DuplicateComponent
    dup2_var = 3, 4

    dup3: DuplicateComponent
    dup3_var = 5, 6

    def createObjects(self):
        self.injectable = Injectable(42)


class SuperComponent:
    intvar: int

    def execute(self):
        pass


class InheritedComponent(SuperComponent):
    tupvar: tuple

    def execute(self):
        pass


class InheritBot(magicbot.MagicRobot):
    component: InheritedComponent

    def createObjects(self):
        self.intvar = 1
        self.tupvar = 1, 2


class BotBase(magicbot.MagicRobot):
    component_a: DumbComponent

    def createObjects(self):
        pass


class InheritedBot(BotBase):
    component_b: DumbComponent


class TypeHintedBot(magicbot.MagicRobot):
    some_int: int = 1
    some_float: float

    component: DumbComponent

    def createObjects(self):
        self.some_float = 0.5


class TypeHintedComponent:
    injectable: Injectable
    numbers: List[float]

    some_int: int = 1
    maybe_float: float = None
    calculated_num: float

    def __init__(self):
        self.calculated_num = 1 - self.some_int
        self.numbers = [1, 2.0, 3, 5.0]

    def execute(self):
        pass


class TypeHintsBot(magicbot.MagicRobot):
    injectable: Injectable
    injectables: List[Injectable]

    component: TypeHintedComponent

    def createObjects(self):
        self.injectable = Injectable(42)
        self.injectables = [self.injectable]


R = TypeVar("R", bound=magicbot.MagicRobot)


def _make_bot(cls: Type[R]) -> R:
    bot = cls()
    bot.createObjects()
    bot._automodes = Mock()
    bot._automodes.modes = {}
    bot._create_components()
    return bot


def test_simple_annotation_inject():
    bot = _make_bot(SimpleBot)

    assert bot.component1.intvar == 1
    assert isinstance(bot.component1.injectable, Injectable)
    assert bot.component1.injectable.num == 42

    assert bot.component2.tupvar == (1, 2)
    assert bot.component2.component1 is bot.component1

    assert bot.component3.intvar == 1
    assert bot.component3.tuple_ == (1, 2)
    assert isinstance(bot.component3.injectable_, Injectable)
    assert bot.component3.injectable_.num == 42
    assert bot.component3.component_2 is bot.component2

    # Check the method hasn't been mutated
    assert str(Component3.__init__.__annotations__["return"]) == "None"


def test_multilevel_annotation_inject():
    bot = _make_bot(MultilevelBot)

    assert bot.dup1 is not bot.dup2
    assert bot.dup1.var == (1, 2)
    assert bot.dup2.var == (3, 4)
    assert bot.dup3.var == (5, 6)


def test_inherited_annotation_inject():
    bot = _make_bot(InheritBot)

    assert bot.component.tupvar == (1, 2)
    assert bot.component.intvar == 1


def test_botinherit_annotation_inject():
    bot = _make_bot(InheritedBot)

    assert isinstance(bot.component_a, DumbComponent)
    assert isinstance(bot.component_b, DumbComponent)
    assert bot.component_a is not bot.component_b


def test_typehintedbot():
    bot = _make_bot(TypeHintedBot)

    assert isinstance(bot.component, DumbComponent)
    assert bot.some_int == 1
    assert bot.some_float == 0.5


def test_typehints_inject():
    bot = _make_bot(TypeHintsBot)

    assert isinstance(bot.component, TypeHintedComponent)
    assert bot.component.some_int == 1
    assert isinstance(bot.component.injectable, Injectable)
    assert bot.component.injectable.num == 42
