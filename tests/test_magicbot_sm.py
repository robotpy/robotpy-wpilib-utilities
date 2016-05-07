
from magicbot.state_machine import (
    state, timed_state,
    AutonomousStateMachine, StateMachine,
    IllegalCallError, NoFirstStateError, MultipleFirstStatesError
)

from magicbot.magic_tunable import setup_tunables

import pytest


def test_no_timed_state_duration():
    with pytest.raises(ValueError):
        class _TM(StateMachine):
            @timed_state()
            def tmp(self):
                pass

def test_no_start_state():
    class _TM(StateMachine):
        pass
    
    with pytest.raises(NoFirstStateError):
        _TM()

def test_multiple_first_states():
    class _TM(StateMachine):
        @state(first=True)
        def tmp1(self):
            pass
        
        @state(first=True)
        def tmp2(self):
            pass
        
    with pytest.raises(MultipleFirstStatesError):
        _TM()

def test_sm(wpitime):
    
    class _TM(StateMachine):

        def __init__(self):
            self.executed = []
    
        def some_fn(self):
            self.executed.append('sf')
        
        @state(first=True)
        def first_state(self):
            self.executed.append(1)
            self.next_state('second_state')
        
        @timed_state(duration=1, next_state='third_state')
        def second_state(self):
            self.executed.append(2)
        
        @state
        def third_state(self):
            self.executed.append(3)
    
    sm = _TM()
    setup_tunables(sm, 'cname')
    sm.some_fn()
    
    # should not be able to directly call
    with pytest.raises(IllegalCallError):
        sm.first_state()
    
    assert sm.current_state == ''
    assert not sm.is_executing
        
    sm.engage()
    assert sm.current_state == 'first_state'
    assert not sm.is_executing
    
    sm.execute()
    assert sm.current_state == 'second_state'
    assert sm.is_executing
    
    # should not change
    sm.engage()
    assert sm.current_state == 'second_state'
    assert sm.is_executing
    
    sm.execute()
    assert sm.current_state == 'second_state'
    assert sm.is_executing
    
    wpitime.now += 1.5
    sm.engage()
    sm.execute()
    assert sm.current_state == 'third_state'
    assert sm.is_executing
    
    sm.engage()
    sm.execute()
    assert sm.current_state == 'third_state'
    assert sm.is_executing
    
    # should be done
    sm.done()
    assert sm.current_state == ''
    assert not sm.is_executing
    
    # should be able to start directly at second state
    sm.engage(initial_state='second_state')
    sm.execute()
    assert sm.current_state == 'second_state'
    assert sm.is_executing
    
    wpitime.now += 1.5
    sm.engage()
    sm.execute()
    assert sm.current_state == 'third_state'
    assert sm.is_executing
    
    # test force
    sm.engage()
    sm.execute()
    assert sm.current_state == 'third_state'
    assert sm.is_executing
    
    sm.engage(force=True)
    assert sm.current_state == 'first_state'
    assert sm.is_executing
    
    sm.execute() 
    sm.execute()
    assert not sm.is_executing
    assert sm.current_state == ''
    
    assert sm.executed == ['sf', 1, 2, 3, 3, 2, 3, 3, 1]

def test_sm_inheritance():
    
    class _TM1(StateMachine):
        @state
        def second_state(self):
            self.done()
    
    class _TM2(_TM1):
        @state(first=True)
        def first_state(self):
            self.next_state('second_state')
    
    sm = _TM2()
    setup_tunables(sm, 'cname')
    sm.engage()
    assert sm.current_state == 'first_state'
    
    sm.execute()
    assert sm.current_state == 'second_state'
    
    sm.execute()
    assert sm.current_state == ''

def test_must_finish():
    class _TM(StateMachine):
        
        def __init__(self):
            self.executed = []
        
        @state(first=True)
        def ordinary1(self):
            self.next_state('ordinary2')
            self.executed.append(1)
            
        @state
        def ordinary2(self):
            self.next_state('must_finish')
            self.executed.append(2)
    
        @state(must_finish=True)
        def must_finish(self):
            self.executed.append('mf')
    
    sm = _TM()
    setup_tunables(sm, 'cname')
    
    sm.engage()
    sm.execute()
    sm.execute()
    
    assert sm.current_state == ''
    assert not sm.is_executing
    
    sm.engage()
    sm.execute()
    sm.engage()
    sm.execute()
    sm.execute()
    sm.execute()
    
    assert sm.current_state == 'must_finish'
    assert sm.is_executing
    
    assert sm.executed == [1, 1, 2, 'mf', 'mf']
    
def test_run_min_duration(wpitime):
    
    class _TM(StateMachine):
        
        @timed_state(first=True, min_duration=2)
        def state1(self, state_tm):
            pass
        
        @state
        def state2(self):
            pass
        
    sm = _TM()
    setup_tunables(sm, 'cname')
    
    sm.engage()
    sm.execute()
    assert sm.current_state == 'state1'
    assert sm.is_executing
    
    wpitime.now += 1
    sm.execute()
    assert sm.current_state == 'state1'
    assert sm.is_executing
    
    wpitime.now += 2
    sm.execute()
    assert sm.current_state == ''
    assert not sm.is_executing

def test_autonomous_sm():
    class _TM(AutonomousStateMachine):
        
        i = 0
        VERBOSE_LOGGING = False
        
        @state(first=True)
        def something(self):
            self.i += 1
            if self.i == 6:
                self.done()
        
    sm = _TM()
    setup_tunables(sm, 'cname')
    
    sm.on_enable()
    
    for _ in range(5):
        sm.on_iteration(None)
        assert sm.is_executing
        
    sm.on_iteration(None)
    assert not sm.is_executing
        
    for _ in range(5):
        sm.on_iteration(None)
        assert not sm.is_executing
    

