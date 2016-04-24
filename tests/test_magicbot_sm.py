
from magicbot.state_machine import (
    state, timed_state,
    StateMachine,
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
        
    sm.begin()
    assert sm.current_state == 'first_state'
    
    sm.execute()
    assert sm.current_state == 'second_state'
    
    # should not go back to the first state
    sm.begin()
    assert sm.current_state == 'second_state'
    
    sm.execute()
    assert sm.current_state == 'second_state'
    
    wpitime.now += 1.5
    sm.execute()
    
    assert sm.current_state == 'third_state'
    sm.execute()
    
    # should be done
    sm.done()
    assert sm.current_state == ''
    
    # should be able to start directly at second state
    sm.begin(initial_state='second_state')
    sm.execute()
    assert sm.current_state == 'second_state'
    
    wpitime.now += 1.5
    sm.execute()
    assert sm.current_state == 'third_state'
    
    # test force
    sm.begin()
    assert sm.current_state == 'third_state'
    sm.begin(force=True)
    assert sm.current_state == 'first_state'
    
    
    assert sm.executed == ['sf', 1, 2, 3, 3, 2, 3]

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
    sm.begin()
    assert sm.current_state == 'first_state'
    
    sm.execute()
    assert sm.current_state == 'second_state'
    
    sm.execute()
    assert sm.current_state == ''
    
    