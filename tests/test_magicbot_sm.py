from magicbot.state_machine import (
    default_state,
    state,
    timed_state,
    AutonomousStateMachine,
    StateMachine,
    IllegalCallError,
    NoFirstStateError,
    MultipleFirstStatesError,
    MultipleDefaultStatesError,
    InvalidStateName,
)

from magicbot.magic_tunable import setup_tunables

import pytest


def test_no_timed_state_duration():
    with pytest.raises(TypeError):

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
            self.executed.append("sf")

        @state(first=True)
        def first_state(self):
            self.executed.append(1)
            self.next_state("second_state")

        @timed_state(duration=1, next_state="third_state")
        def second_state(self):
            self.executed.append(2)

        @state
        def third_state(self):
            self.executed.append(3)

    sm = _TM()
    setup_tunables(sm, "cname")
    sm.some_fn()

    # should not be able to directly call
    with pytest.raises(IllegalCallError):
        sm.first_state()

    assert sm.current_state == ""
    assert not sm.is_executing

    sm.engage()
    assert sm.current_state == "first_state"
    assert not sm.is_executing

    sm.execute()
    assert sm.current_state == "second_state"
    assert sm.is_executing

    # should not change
    sm.engage()
    assert sm.current_state == "second_state"
    assert sm.is_executing

    sm.execute()
    assert sm.current_state == "second_state"
    assert sm.is_executing

    wpitime.step(1.5)
    sm.engage()
    sm.execute()
    assert sm.current_state == "third_state"
    assert sm.is_executing

    sm.engage()
    sm.execute()
    assert sm.current_state == "third_state"
    assert sm.is_executing

    # should be done
    sm.done()
    assert sm.current_state == ""
    assert not sm.is_executing

    # should be able to start directly at second state
    sm.engage(initial_state="second_state")
    sm.execute()
    assert sm.current_state == "second_state"
    assert sm.is_executing

    wpitime.step(1.5)
    sm.engage()
    sm.execute()
    assert sm.current_state == "third_state"
    assert sm.is_executing

    # test force
    sm.engage()
    sm.execute()
    assert sm.current_state == "third_state"
    assert sm.is_executing

    sm.engage(force=True)
    assert sm.current_state == "first_state"
    assert sm.is_executing

    sm.execute()
    sm.execute()
    assert not sm.is_executing
    assert sm.current_state == ""

    assert sm.executed == ["sf", 1, 2, 3, 3, 2, 3, 3, 1]


def test_sm_inheritance():
    class _TM1(StateMachine):
        @state
        def second_state(self):
            self.done()

    class _TM2(_TM1):
        @state(first=True)
        def first_state(self):
            self.next_state("second_state")

    sm = _TM2()
    setup_tunables(sm, "cname")
    sm.engage()
    assert sm.current_state == "first_state"

    sm.execute()
    assert sm.current_state == "second_state"

    sm.execute()
    assert sm.current_state == ""


def test_must_finish(wpitime):
    class _TM(StateMachine):
        def __init__(self):
            self.executed = []

        @state(first=True)
        def ordinary1(self):
            self.next_state("ordinary2")
            self.executed.append(1)

        @state
        def ordinary2(self):
            self.next_state("must_finish")
            self.executed.append(2)

        @state(must_finish=True)
        def must_finish(self):
            self.executed.append("mf")

        @state
        def ordinary3(self):
            self.executed.append(3)
            self.next_state_now("timed_must_finish")

        @timed_state(duration=1, must_finish=True)
        def timed_must_finish(self):
            self.executed.append("tmf")

    sm = _TM()
    setup_tunables(sm, "cname")

    sm.engage()
    sm.execute()
    sm.execute()

    assert sm.current_state == ""
    assert not sm.is_executing

    sm.engage()
    sm.execute()
    sm.engage()
    sm.execute()
    sm.execute()
    sm.execute()

    assert sm.current_state == "must_finish"
    assert sm.is_executing

    sm.next_state("ordinary3")
    sm.engage()
    sm.execute()

    assert sm.current_state == "timed_must_finish"

    sm.execute()
    assert sm.is_executing
    assert sm.current_state == "timed_must_finish"

    for _ in range(7):
        wpitime.step(0.1)

        sm.execute()
        assert sm.is_executing
        assert sm.current_state == "timed_must_finish"

    wpitime.step(1)
    sm.execute()
    assert not sm.is_executing

    assert sm.executed == [1, 1, 2, "mf", "mf", 3] + ["tmf"] * 9


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
    setup_tunables(sm, "cname")

    sm.on_enable()

    for _ in range(5):
        sm.on_iteration(None)
        assert sm.is_executing

    sm.on_iteration(None)
    assert not sm.is_executing

    for _ in range(5):
        sm.on_iteration(None)
        assert not sm.is_executing

    assert sm.i == 6


def test_autonomous_sm_end_timed_state(wpitime):
    class _TM(AutonomousStateMachine):

        i = 0
        j = 0
        VERBOSE_LOGGING = False

        @state(first=True)
        def something(self):
            self.i += 1
            if self.i == 3:
                self.next_state("timed")

        @timed_state(duration=1)
        def timed(self):
            self.j += 1

    sm = _TM()
    setup_tunables(sm, "cname")

    sm.on_enable()

    for _ in range(5):
        wpitime.step(0.7)
        sm.on_iteration(None)
        assert sm.is_executing

    for _ in range(5):
        wpitime.step(0.7)
        sm.on_iteration(None)
        assert not sm.is_executing

    assert sm.i == 3
    assert sm.j == 2


def test_next_fn():
    class _TM(StateMachine):
        @state(first=True)
        def first_state(self):
            self.next_state(self.second_state)

        @state
        def second_state(self):
            self.done()

    sm = _TM()
    setup_tunables(sm, "cname")
    sm.engage()
    assert sm.current_state == "first_state"

    sm.execute()
    assert sm.current_state == "second_state"

    sm.engage()
    sm.execute()
    assert sm.current_state == ""


def test_next_fn2(wpitime):
    class _TM(StateMachine):
        @state
        def second_state(self):
            pass

        @timed_state(first=True, duration=0.1, next_state=second_state)
        def first_state(self):
            pass

    sm = _TM()
    setup_tunables(sm, "cname")
    sm.engage()
    sm.execute()
    assert sm.current_state == "first_state"
    assert sm.is_executing

    wpitime.step(0.5)

    sm.engage()
    sm.execute()
    assert sm.current_state == "second_state"
    assert sm.is_executing

    sm.execute()
    assert sm.current_state == ""
    assert not sm.is_executing


def test_mixup():
    from robotpy_ext.autonomous import state as _ext_state
    from robotpy_ext.autonomous import timed_state as _ext_timed_state

    with pytest.raises(RuntimeError) as exc_info:

        class _SM1(StateMachine):
            @_ext_state(first=True)
            def the_state(self):
                pass

    assert isinstance(exc_info.value.__cause__, TypeError)

    with pytest.raises(RuntimeError) as exc_info:

        class _SM2(StateMachine):
            @_ext_timed_state(first=True, duration=1)
            def the_state(self):
                pass

    assert isinstance(exc_info.value.__cause__, TypeError)


def test_forbidden_state_names():
    with pytest.raises(InvalidStateName):

        class _SM(StateMachine):
            @state
            def done(self):
                pass


def test_mixins():
    class _SM1(StateMachine):
        @state
        def state1(self):
            pass

    class _SM2(StateMachine):
        @state
        def state2(self):
            pass

    class _SM(_SM1, _SM2):
        @state(first=True)
        def first_state(self):
            pass

    s = _SM()
    states = s._StateMachine__states

    assert "state1" in states
    assert "state2" in states
    assert "first_state" in states


def test_multiple_default_states():
    class _SM(StateMachine):
        @state(first=True)
        def state(self):
            pass

        @default_state
        def state1(self):
            pass

        @default_state
        def state2(self):
            pass

    with pytest.raises(MultipleDefaultStatesError):
        _SM()


def test_default_state_machine():
    class _SM(StateMachine):
        def __init__(self):
            self.didOne = None
            self.didDefault = None
            self.defaultInit = None
            self.didDone = None

        @state(first=True)
        def stateOne(self):
            self.didOne = True
            self.didDefault = False
            self.didDone = False

        @state
        def doneState(self):
            self.didOne = False
            self.didDefault = False
            self.didDone = True
            self.done()

        @default_state
        def defaultState(self, initial_call):
            self.didOne = False
            self.didDefault = True
            self.defaultInit = initial_call
            self.didDone = False

    sm = _SM()
    setup_tunables(sm, "cname")

    sm.execute()
    assert sm.didOne == False
    assert sm.didDefault == True
    assert sm.defaultInit == True
    assert sm.didDone == False

    sm.execute()
    assert sm.didOne == False
    assert sm.didDefault == True
    assert sm.defaultInit == False
    assert sm.didDone == False

    # do a thing
    sm.engage()
    sm.execute()
    assert sm.didOne == True
    assert sm.didDefault == False
    assert sm.didDone == False

    # should go back (test for initial)
    sm.execute()
    assert sm.didOne == False
    assert sm.didDefault == True
    assert sm.defaultInit == True
    assert sm.didDone == False

    # should happen again (no initial)
    sm.execute()
    assert sm.didOne == False
    assert sm.didDefault == True
    assert sm.defaultInit == False
    assert sm.didDone == False

    # do another thing
    sm.engage()
    sm.execute()
    assert sm.didOne == True
    assert sm.didDefault == False
    assert sm.didDone == False

    # should go back (test for initial)
    sm.execute()
    assert sm.didOne == False
    assert sm.didDefault == True
    assert sm.defaultInit == True
    assert sm.didDone == False

    # should happen again (no initial)
    sm.execute()
    assert sm.didOne == False
    assert sm.didDefault == True
    assert sm.defaultInit == False
    assert sm.didDone == False

    # enagage a state that will call done, check to see
    # if we come back
    sm.engage("doneState")
    sm.execute()
    assert sm.didOne == False
    assert sm.didDefault == False
    assert sm.defaultInit == False
    assert sm.didDone == True

    # should go back (test for initial)
    sm.execute()
    assert sm.didOne == False
    assert sm.didDefault == True
    assert sm.defaultInit == True
    assert sm.didDone == False

    # should happen again (no initial)
    sm.execute()
    assert sm.didOne == False
    assert sm.didDefault == True
    assert sm.defaultInit == False
    assert sm.didDone == False


def test_short_timed_state(wpitime):
    """
    Tests two things:
    - A timed state that expires before it executes
    - Ensures that the default state won't execute if the machine is always
      executing
    """

    class _SM(StateMachine):
        def __init__(self):
            self.executed = []

        @default_state
        def d(self):
            self.executed.append("d")

        @state(first=True)
        def a(self):
            self.executed.append("a")
            self.next_state("b")

        @timed_state(duration=0.01)
        def b(self):
            self.executed.append("b")

        def done(self):
            super().done()
            self.executed.append("d")

    sm = _SM()
    setup_tunables(sm, "cname")
    assert sm.current_state == ""
    assert not sm.is_executing

    for _ in [1, 2, 3, 4]:
        sm.engage()
        sm.execute()
        assert sm.current_state == "b"

        wpitime.step(0.02)

        sm.engage()
        sm.execute()
        assert sm.current_state == "b"

        wpitime.step(0.02)

    assert sm.executed == ["a", "b", "d", "a", "b", "d", "a", "b", "d", "a", "b"]
