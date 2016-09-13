import wpilib.command

class Command(wpilib.command.Command):
    '''
    Provides a generic base so you only need to implement what is unique to
    your command. If you don't override isFinished(), your command will never
    end naturally. It can still be interrupted by a conflicting command or
    cancelled manually.
    '''

    def __init__(self, name, timeoutInSeconds=None):
        super().__init__(name, timeoutInSeconds)


    def initialize(self):
        pass


    def execute(self):
        pass


    def isFinished(self):
        return False


    def end(self):
        pass


    def interrupted(self):
        self.end()
