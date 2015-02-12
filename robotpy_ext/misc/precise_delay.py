
import hal
import time
import wpilib


class PreciseDelay:
    '''
        Used to synchronize a timing loop. Will delay precisely so that
        the next invocation of your loop happens at the same period, as long
        as your code does not run longer than the length of the delay.
        
        Our experience has shown that 25ms is a good loop period.
    
        Usage::
        
            delay = PreciseDelay(time_to_delay)
            
            while something:
                # do things here
                delay.wait()
    '''
    
    def __init__(self, delay_period):
        '''
            :param delay_period: The amount of time (in seconds) to do a delay
            :type delay_period: float
        '''
        
        # The WPILib sleep/etc functions are slightly less stable as
        # they have more overhead, so only use them in simulation mode
        if hal.HALIsSimulation:
            self.delay = wpilib.Timer.delay
            self.get_now = wpilib.Timer.getFPGATimestamp
        else:
            self.delay = time.sleep
            self.get_now = time.time  
        
        self.delay_period = float(delay_period)
        if self.delay_period < 0.001:
            raise ValueError("You probably don't want to delay less than 1ms!")
        
        self.next_delay = self.get_now() + self.delay_period
        
    def wait(self):
        '''Waits until the delay period has passed'''
        
        # optimization -- avoid local lookups
        delay = self.delay
        get_now = self.get_now
        next_delay = self.next_delay
        
        while True:
            # we must *always* yield here, so other things can run
            delay(0.0002)
            
            if next_delay < get_now():
                break
        
        self.next_delay += self.delay_period
