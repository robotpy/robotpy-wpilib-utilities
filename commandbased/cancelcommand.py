from wpilib.command import Command


def checkIfCanceled(self):
    if self.forceCancel:
        self.forceCancel = False
        return True

    return self._isFinished()


class CancelCommand(Command):
    """
    When this command is run, it cancels the command it was passed.
    """

    def __init__(self, command: Command):
        """
        :param command: The command to cancel.
        """
        super().__init__("Cancel %s" % command)

        self.command = command

    def initialize(self):
        if self.command.isRunning():
            self.command.cancel()

    def isFinished(self):
        return not self.command.isRunning()
