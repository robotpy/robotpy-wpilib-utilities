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


class SimpleBot(magicbot.MagicRobot):
    intvar = 1
    tupvar = 1, 2

    component1: Component1
    component2: Component2

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

    component: DumbComponent

    def createObjects(self):
        pass


class TypeHintedComponent:
    injectable: Injectable

    some_int: int = 1

    def execute(self):
        pass


class TypeHintsBot(magicbot.MagicRobot):
    component: TypeHintedComponent

    def createObjects(self):
        self.injectable = Injectable(42)
