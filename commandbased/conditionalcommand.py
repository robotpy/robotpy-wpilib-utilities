from wpilib.command.commandgroup import CommandGroup


class ConditionalCommand(CommandGroup):
    def __init__(self, name, onTrue=None, onFalse=None):
        super().__init__(name)

        self.onTrue = self._processCommand(onTrue)
        self.onFalse = self._processCommand(onFalse)

    def _processCommand(self, cmd):
        if cmd is None:
            return []

        with self.mutex:
            if self.locked:
                raise ValueError("Cannot add conditions to ConditionalCommand")

            for reqt in cmd.getRequirements():
                self.requires(reqt)

            cmd.setParent(self)
            cmd = CommandGroup.Entry(cmd, CommandGroup.Entry.IN_SEQUENCE, None)
            return [cmd]

    def _initialize(self):
        super()._initialize()

        if self.condition():
            self.commands = self.onTrue
        else:
            self.commands = self.onFalse
