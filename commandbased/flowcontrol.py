"""
These functions can be used to make programming CommandGroups much more
intuitive. For more information, check each method's docstring.
"""

from wpilib.command import Command, CommandGroup, ConditionalCommand
from commandbased.cancelcommand import CancelCommand

import inspect

__all__ = ["IF", "ELIF", "ELSE", "WHILE", "RETURN", "BREAK", "CommandFlow"]


class ConditionalFlow(ConditionalCommand):
    def __init__(self, name, onTrue, onFalse, condition):
        ConditionalCommand.__init__(self, name, onTrue, onFalse)

        self.flowCondition = condition

    def _condition(self):
        return self.flowCondition()


class CommandFlow(CommandGroup):
    def __init__(self, name):
        CommandGroup.__init__(self, name)

        callingFlow = _getCommandFlow()
        self._source = getattr(callingFlow, "_source", self)
        self._ifStack = None

    def _popIfStack(self):
        """
        We buffer conditionals until the last moment so we don't have trouble with
        Commands being locked when they're added to a CommandGroup.
        """
        if self._ifStack:
            top = self._ifStack.pop(0)
            cmd = None
            for x in reversed(self._ifStack):
                if x[0]:
                    cmd = ConditionalFlow("flowcontrolELIF", x[1], cmd, x[0])

                else:
                    cmd = x[1]

            cmd = ConditionalFlow("flowcontrolIF", top[1], cmd, top[0])

            self._ifStack = None
            self.addSequential(cmd)

    # These _hook methods ensure we always add our buffered conditions
    def addSequential(self, cmd, timeout=None):
        self._popIfStack()
        if timeout is None:
            CommandGroup.addSequential(self, cmd)
        else:
            CommandGroup.addSequential(self, cmd, timeout)

    def addParallel(self, cmd, timeout=None):
        self._popIfStack()
        if timeout is None:
            CommandGroup.addParallel(self, cmd)
        else:
            CommandGroup.addParallel(self, cmd, timeout)

    def start(self):
        self._popIfStack()
        CommandGroup.start(self)

    def setParent(self, parent):
        self._popIfStack()
        CommandGroup.setParent(self, parent)


class CommandFlowWhile(CommandFlow):
    def __init__(self, name, condition):
        super().__init__(name)

        self.whileCondition = condition

    def isFinished(self):
        if CommandGroup.isFinished(self):
            if not self.whileCondition():
                return True

            self.start()

        return False


def _getCommandFlow():
    """
    Does some rather ugly stack inspection to find out which CommandGroup the
    calling function was triggered from.
    """
    # https://stackoverflow.com/a/14694234
    stack = inspect.stack()
    frame = stack[2].frame
    while "self" not in frame.f_locals:
        frame = frame.f_back
        if frame is None:
            raise ValueError("Could not find calling class for %s" % stack[1].function)

    cg = frame.f_locals["self"]
    if not isinstance(cg, CommandFlow):
        raise ValueError(
            "%s may not be used outside of a CommandFlow" % stack[1].function
        )

    return cg


def _buildCommandFlow(func, parent):
    """Turns the given function into a full CommandGroup."""
    cg = CommandFlow(func.__name__)
    func(cg)

    return cg


def IF(condition):
    """
    Use as a decorator for a function. That function will be placed into a
    CommandGroup and run inside a ConditionalCommand with the given condition.
    The decorated function must accept one positional argument that will be used
    as its 'self'.
    """

    def flowcontrolIF(func):
        parent = _getCommandFlow()
        cg = _buildCommandFlow(func, parent)

        try:
            parent._popIfStack()
        except AttributeError:
            pass

        parent._ifStack = [(condition, cg)]

    return flowcontrolIF


def ELIF(condition):
    """
    Use as a decorator for a function. That function will be placed into a
    CommandGroup which will be triggered by a ConditionalCommand that uses the
    passed condition. That ConditionalCommand will then be added as the onFalse
    for the ConditionalCommand created by a previous IF or ELIF.
    """

    def flowcontrolELIF(func):
        parent = _getCommandFlow()
        cg = _buildCommandFlow(func, parent)

        try:
            parent._ifStack.append((condition, cg))
        except AttributeError:
            raise ValueError("Cannot use ELIF without IF")

    return flowcontrolELIF


def ELSE(func):
    """
    Use as a decorator for a function. That function will be placed into a
    CommandGroup which will be added as the onFalse for the ConditionalCommand
    created by a previous IF or ELIF.
    """

    parent = _getCommandFlow()
    cg = _buildCommandFlow(func, parent)

    try:
        parent._ifStack.append((None, cg))
    except AttributeError:
        raise ValueError("Cannot use ELSE without IF")

    parent._popIfStack()


def WHILE(condition):
    """
    Use as a decorator for a function. That function will be placed into a
    CommandGroup, which will be added to a ConditionalCommand. It will be
    modified to restart itself automatically.
    """
    raise NotImplementedError("WHILE does not yet work with Commands v1")


def RETURN():
    """
    Calling this function will end the source CommandGroup immediately.
    """

    parent = _getCommandFlow()
    parent.addSequential(CancelCommand(parent._source))


def BREAK(steps=1):
    """
    Calling this function will end the loop that contains it. Pass an integer to
    break out of that number of nested loops.
    """
    raise ValueError("Cannot BREAK outside of a loop")
