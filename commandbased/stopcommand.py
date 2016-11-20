from wpilib.command import InstantCommand

class StopCommand(InstantCommand):
    '''
    When this command is run, it cancels the command it was passed, even if that
    command is part of a :class:`wpilib.CommandGroup`.
    '''


    def __init__(self, command):
        '''
            :param command: The :class:`wpilib.Command` to stop.
        '''
        super().__init__('Stop %s' % command)

        self.command = command


    def initialize(self):
        self.command._cancel()
