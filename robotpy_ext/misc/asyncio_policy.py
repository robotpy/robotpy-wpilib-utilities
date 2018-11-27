"""
This is a replacement event loop and policy for asyncio that uses FPGA time,
rather than native python time.
"""
from asyncio.events import AbstractEventLoopPolicy
from asyncio import SelectorEventLoop, set_event_loop_policy
from wpilib import Timer


class FPGATimedEventLoop(SelectorEventLoop):
    """An asyncio event loop that uses wpilib time rather than python time"""

    def time(self):
        return Timer.getFPGATimestamp()


class FPGATimedEventLoopPolicy(AbstractEventLoopPolicy):
    """An asyncio event loop policy that uses FPGATimedEventLoop"""

    _loop_factory = FPGATimedEventLoop


def patch_asyncio_policy():
    """
    Sets an instance of FPGATimedEventLoopPolicy as the default asyncio event
    loop policy
    """
    set_event_loop_policy(FPGATimedEventLoopPolicy())
