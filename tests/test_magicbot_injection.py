import sys
import magicbot

class Injectable:
    def __init__(self, num):
        self.num = num

def test_simple_inject():
    
    class Component1:
        
        intvar = int
        tupvar = tuple
        
        injectable = Injectable
        
        def execute(self):
            pass
            
    class Component2:
        
        tupvar = tuple
        
        component1 = Component1
        
        def execute(self):
            pass
    
    class Bot(magicbot.MagicRobot):
        
        intvar = 1
        tupvar = (1,2)
        
        component1 = Component1
        component2 = Component2
        
        def createObjects(self):
            self.injectable = Injectable(42)
    
    bot = Bot()
    bot.robotInit()
    
    assert bot.component1.intvar == 1
    assert isinstance(bot.component1.injectable, Injectable)
    assert bot.component1.injectable.num == 42
    
    assert bot.component2.tupvar == (1,2)
    assert bot.component2.component1 is bot.component1


def test_multilevel_inject():
    
    class DuplicateComponent:
        
        var = tuple
        injectable = Injectable
        
        def execute(self):
            pass

    class Bot(magicbot.MagicRobot):
        
        dup1 = DuplicateComponent
        dup1_var = (1,2)
        
        dup2 = DuplicateComponent
        dup2_var = (3,4)
        
        dup3 = DuplicateComponent
        dup3_var = (5,6)
        
        def createObjects(self):
            self.injectable = Injectable(42)

    bot = Bot()
    bot.robotInit()
    
    assert bot.dup1.var == (1,2)
    assert bot.dup2.var == (3,4)
    assert bot.dup3.var == (5,6)


def test_inherited_inject():
    class SuperComponent:
        intvar = int

        def execute(self):
            pass

    class Component(SuperComponent):
        tupvar = tuple

        def execute(self):
            pass

    class Bot(magicbot.MagicRobot):
        component = Component

        def createObjects(self):
            self.intvar = 1
            self.tupvar = (1, 2)

    bot = Bot()
    bot.robotInit()

    assert bot.component.tupvar == (1, 2)
    assert bot.component.intvar == 1


def test_botinherit_inject():
    class Component:
        def execute(self):
            pass

    class BotBase(magicbot.MagicRobot):
        component_a = Component

        def createObjects(self):
            pass

    class Bot(BotBase):
        component_b = Component

    bot = Bot()
    bot.robotInit()

    assert isinstance(bot.component_a, Component)
    assert isinstance(bot.component_b, Component)
    assert bot.component_a is not bot.component_b


# Variable annotations are a Python 3.6+ feature
if sys.version_info >= (3, 6):
    def test_simple_annotation_inject():
        from magicbot_annotation_tester import SimpleBot, Injectable

        bot = SimpleBot()
        bot.robotInit()

        assert bot.component1.intvar == 1
        assert isinstance(bot.component1.injectable, Injectable)
        assert bot.component1.injectable.num == 42

        assert bot.component2.tupvar == (1, 2)
        assert bot.component2.component1 is bot.component1

    def test_multilevel_annotation_inject():
        from magicbot_annotation_tester import MultilevelBot

        bot = MultilevelBot()
        bot.robotInit()

        assert bot.dup1 is not bot.dup2
        assert bot.dup1.var == (1, 2)
        assert bot.dup2.var == (3, 4)
        assert bot.dup3.var == (5, 6)

    def test_inherited_annotation_inject():
        from magicbot_annotation_tester import InheritBot

        bot = InheritBot()
        bot.robotInit()

        assert bot.component.tupvar == (1, 2)
        assert bot.component.intvar == 1

    def test_botinherit_annotation_inject():
        from magicbot_annotation_tester import InheritedBot, DumbComponent

        bot = InheritedBot()
        bot.robotInit()

        assert isinstance(bot.component_a, DumbComponent)
        assert isinstance(bot.component_b, DumbComponent)
        assert bot.component_a is not bot.component_b

    def test_typehintedbot():
        from magicbot_annotation_tester import TypeHintedBot, DumbComponent

        bot = TypeHintedBot()
        bot.robotInit()

        assert isinstance(bot.component, DumbComponent)
        assert bot.some_int == 1
        assert bot.some_float == 0.5

    def test_typehints_inject():
        from magicbot_annotation_tester import TypeHintsBot, TypeHintedComponent, Injectable

        bot = TypeHintsBot()
        bot.robotInit()

        assert isinstance(bot.component, TypeHintedComponent)
        assert bot.component.some_int == 1
        assert isinstance(bot.component.injectable, Injectable)
        assert bot.component.injectable.num == 42
