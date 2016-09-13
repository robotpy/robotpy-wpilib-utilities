from .command import Command

class InstantCommand(Command):
    '''
    A command that has no duration. Subclasses should implement the initialize()
    method to carry out desired actions.
    '''

    def __init__(self, name):
        super().__init__(name)


    def isFinished(self):
        return True

