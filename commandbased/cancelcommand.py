from wpilib.command import Command


def checkIfCanceled(self):
    if self.forceCancel:
        self.forceCancel = False
        return True

    return self._isFinished()


class CancelCommand(Command):
    """
    When this command is run, it cancels the command it was passed, even if that
    command is part of a :class:`wpilib.CommandGroup`.
    """

    def __init__(self, command):
        """
            :param command: The :class:`wpilib.Command` to cancel.
        """
        super().__init__("Cancel %s" % command)

        self.command = command
        if hasattr(self.command, "_isFinished"):
            return

        self.command._isFinished = self.command.isFinished
        self.command.isFinished = checkIfCanceled.__get__(self.command)
        self.command.forceCancel = False

    def initialize(self):
        if self.command.isRunning():
            self.command.forceCancel = True

    def isFinished(self):
        return not self.command.isRunning()
