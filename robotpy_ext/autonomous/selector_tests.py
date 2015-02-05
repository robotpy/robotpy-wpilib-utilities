
from networktables.util import ChooserControl

autonomous_seconds = 15

def test_all_autonomous(control, fake_time, robot):
    '''
        This test runs all possible autonomous modes that can be selected
        by the autonomous switcher.
        
        This should work for most robots. If it doesn't work for yours, 
        and it's not a code issue with your robot, please file a bug on
        github.
    '''
    
    class AutonomousTester:
        
        def __init__(self):
            self.initialized = False
            
            self.state = 'auto'
            self.currentChoice = None
            self.until = None
        
        def initialize_chooser(self, tm):
            self.initialized = True
            self.chooser = ChooserControl('Autonomous Mode')
            self.choices = self.chooser.getChoices()
            
            self.state = 'disabled'
            self.currentChoice =  -1
            self.until = tm
        
        def on_step(self, tm):
            
            if not self.initialized:
                self.initialize_chooser(tm)
            
            if self.state == 'auto':
                if tm >= self.until:
                    self.until = tm + 1
                    self.state = 'disabled'
                    control.set_operator_control(enabled=False)
            
            elif self.state == 'disabled':
                if tm >= self.until:
                    
                    control.set_autonomous()
                    
                    self.state = 'auto'
                    self.until = tm + autonomous_seconds
                    self.currentChoice += 1
                    if self.currentChoice >= len(self.choices):
                        return False
                    
                    self.chooser.setSelected(self.choices[self.currentChoice])
            
            return True
    
    
    controller = control.run_test(AutonomousTester)
    
    # Make sure they ran for the correct amount of time
    assert int(fake_time.get()) == len(controller.choices)*(autonomous_seconds+1)
