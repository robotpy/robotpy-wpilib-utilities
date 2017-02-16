
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
