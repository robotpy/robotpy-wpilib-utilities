from .magicrobot import MagicRobot
from .magic_tunable import feedback, tunable
from .magic_reset import will_reset_to

from .state_machine import (
    AutonomousStateMachine,
    StateMachine,
    default_state,
    state,
    timed_state,
)

__all__ = (
    "MagicRobot",
    "feedback",
    "tunable",
    "will_reset_to",
    "AutonomousStateMachine",
    "StateMachine",
    "default_state",
    "state",
    "timed_state",
)
