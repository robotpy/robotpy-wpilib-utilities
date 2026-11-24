from components import AutoCommands


class LibraryAuto:
    MODE_NAME = "Library command"
    DEFAULT = True

    auto_commands: AutoCommands

    def on_enable(self):
        self.auto_commands.start()

    def on_iteration(self, time_elapsed):
        pass  # The component and CommandRunner do the work.

    def on_disable(self):
        # Also handles a direct autonomous-to-teleop transition.
        self.auto_commands.stop()
