from .magic_reset import will_reset_to
from .magic_tunable import feedback, tunable
from .magicrobot import MagicRobot
from .state_machine import (
    AutonomousStateMachine,
    StateMachine,
    default_state,
    state,
    timed_state,
)

__all__ = (
    "AutonomousStateMachine",
    "MagicRobot",
    "StateMachine",
    "default_state",
    "feedback",
    "state",
    "timed_state",
    "tunable",
    "will_reset_to",
)
