"""
    Demonstrates chaining multiple autonomous modes together
"""


from robotpy_ext.autonomous import StatefulAutonomous, state, state_alias, timed_state

class Auto1(StatefulAutonomous):
    @timed_state(duration=1, next_state='do1_2')
    def do1_1(self):
        pass
    
    @timed_state(duration=1, next_state='transition')
    def do1_2(self):
        pass
    

class Auto2(StatefulAutonomous):
    @timed_state(duration=1, next_state='do2_2')
    def do2_1(self):
        pass
    
    @timed_state(duration=1)
    def do2_2(self):
        pass


class ChainedMode(Auto1, Auto2):
    '''Chains two autonomous modes together'''
    
    MODE_NAME = "ChainedMode"
    
    start = state_alias(Auto1.do1_1, first=True)
    transition = state_alias(Auto2.do2_2)
    
class SingleMode(Auto1):
    '''Runs one of the chained autonomous modes by itself'''
    
    MODE_NAME = "Single"
    
    start = state_alias(Auto1.do1_1, first=True)
    
    @state()
    def transition(self):
        pass
