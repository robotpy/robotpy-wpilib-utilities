import pytest

from wpilib.command import Scheduler, InstantCommand, CommandGroup

import commandbased.flowcontrol as fc


def run_command(cmd):
    cmd.start()

    scheduler = Scheduler.getInstance()
    for x in range(0, 2000):
        scheduler.run()
        if not cmd.isRunning():
            return True

    return False


class CounterCommand(InstantCommand):
    def __init__(self):
        super().__init__('Counter')
        self.counter = 0

    def initialize(self):
        self.counter += 1


def test_if():
    cmd1 = CounterCommand()
    cmd2 = CounterCommand()

    class IfCommand(CommandGroup):
        def __init__(self):
            nonlocal cmd1, cmd2

            super().__init__('Test IF')
            self.setRunWhenDisabled(True)

            @fc.IF(lambda: False)
            def increment_cmd1(self):
                self.addSequential(cmd1)

            @fc.IF(lambda: True)
            def increment_cmd2(self):
                self.addSequential(cmd2)


    cmd = IfCommand()

    assert run_command(cmd)
    assert cmd1.counter == 0
    assert cmd2.counter == 1


def test_elif():
    cmd1 = CounterCommand()
    cmd2 = CounterCommand()
    cmd3 = CounterCommand()

    class ElifCommand(CommandGroup):
        def __init__(self):
            nonlocal cmd1, cmd2, cmd3

            super().__init__('Test ELIF')
            self.setRunWhenDisabled(True)

            @fc.IF(lambda: False)
            def increment_cmd1(self):
                self.addSequential(cmd1)

            @fc.ELIF(lambda: True)
            def increment_cmd2(self):
                self.addSequential(cmd2)

            @fc.ELIF(lambda: True)
            def increment_cmd3(self):
                self.addSequential(cmd3)

    cmd = ElifCommand()

    assert run_command(cmd)
    assert cmd1.counter == 0
    assert cmd2.counter == 1
    assert cmd3.counter == 0


def test_else():
    cmd1 = CounterCommand()
    cmd2 = CounterCommand()
    cmd3 = CounterCommand()

    class ElseCommand(CommandGroup):
        def __init__(self):
            nonlocal cmd1, cmd2, cmd3

            super().__init__('Test ELSE')
            self.setRunWhenDisabled(True)

            @fc.IF(lambda: False)
            def increment_cmd1(self):
                self.addSequential(cmd1)

            @fc.ELIF(lambda: False)
            def increment_cmd2(self):
                self.addSequential(cmd2)


            @fc.ELSE
            def increment_cmd3(self):
                self.addSequential(cmd3)

    cmd = ElseCommand()

    assert run_command(cmd)
    assert cmd1.counter == 0
    assert cmd2.counter == 0
    assert cmd3.counter == 1


def test_while():
    cmd1 = CounterCommand()

    class WhileCommand(CommandGroup):
        def __init__(self):
            nonlocal cmd1

            super().__init__('Test WHILE')
            self.setRunWhenDisabled(True)

            x = 5
            def do_loop():
                nonlocal x

                x -= 1

                return x > 0

            @fc.WHILE(do_loop)
            def count_to_four(self):
                self.addSequential(cmd1)

    cmd = WhileCommand()

    assert run_command(cmd)
    assert cmd1.counter == 4


def test_break():
    cmd1 = CounterCommand()
    cmd2 = CounterCommand()

    class BreakCommand(CommandGroup):
        def __init__(self):
            nonlocal cmd1, cmd2

            super().__init__('Test BREAK')
            self.setRunWhenDisabled(True)

            x = 5
            def do_loop():
                nonlocal x

                x -= 1

                return x > 0

            @fc.WHILE(do_loop)
            def count_to_four(self):
                self.addSequential(cmd1)

                @fc.IF(lambda: x == 3)
                def breakLoop(self):
                    fc.BREAK()

            self.addSequential(cmd2)

    cmd = BreakCommand()

    assert run_command(cmd)
    assert cmd1.counter == 2
    assert cmd2.counter == 1


def test_return():
    cmd1 = CounterCommand()
    cmd2 = CounterCommand()
    cmd3 = CounterCommand()
    cmd4 = CounterCommand()
    cmd5 = CounterCommand()
    cmd6 = CounterCommand()

    class ReturnCommand(CommandGroup):
        def __init__(self):
            nonlocal cmd1, cmd2, cmd3, cmd4, cmd5, cmd6

            super().__init__('Test RETURN')
            self.setRunWhenDisabled(True)

            self.addSequential(cmd1)

            @fc.IF(lambda: True)
            def increment_cmd2(self):
                self.addSequential(cmd2)
                @fc.IF(lambda: True)
                def increment_cmd3(self):
                    self.addSequential(cmd3)
                    @fc.IF(lambda: True)
                    def do_return(self):
                        fc.RETURN()
                    self.addSequential(cmd4)
                self.addSequential(cmd5)
            self.addSequential(cmd6)

    cmd = ReturnCommand()

    assert run_command(cmd)
    assert cmd1.counter == 1
    assert cmd2.counter == 1
    assert cmd3.counter == 1
    assert cmd4.counter == 0
    assert cmd5.counter == 0
    assert cmd6.counter == 0


def test_break2():
    cmd1 = CounterCommand()
    cmd2 = CounterCommand()
    cmd3 = CounterCommand()

    class BreakCommand(CommandGroup):
        def __init__(self):
            nonlocal cmd1, cmd2, cmd3

            super().__init__('Test BREAK 2')
            self.setRunWhenDisabled(True)

            x = 5
            def do_loop():
                nonlocal x

                x -= 1

                if x == 0:
                    x = 10
                    return False

                return True

            @fc.WHILE(lambda: True)
            def loop_forever(self):
                self.addSequential(cmd1)
                @fc.WHILE(do_loop)
                def count_to_four(self):
                    self.addSequential(cmd2)

                    @fc.IF(lambda: x == 5)
                    def breakLoop(self):
                        fc.BREAK(2)

            self.addSequential(cmd3)

    cmd = BreakCommand()

    assert run_command(cmd)
    assert cmd1.counter == 2
    assert cmd2.counter == 9
    assert cmd3.counter == 1


def test_contained_return():
    cmd1 = CounterCommand()
    cmd2 = CounterCommand()
    cmd3 = CounterCommand()
    cmd4 = CounterCommand()

    class ReturnCommand(CommandGroup):
        def __init__(self):
            nonlocal cmd2, cmd3

            super().__init__('Test RETURN')
            self.setRunWhenDisabled(True)

            self.addSequential(cmd2)
            fc.RETURN()
            self.addSequential(cmd3)

    class ContainerCommand(CommandGroup):
        def __init__(self):
            nonlocal cmd1, cmd4

            super().__init__('Test Contained RETURN')
            self.setRunWhenDisabled(True)

            self.addSequential(cmd1)
            self.addSequential(ReturnCommand())
            self.addSequential(cmd4)


    cmd = ContainerCommand()

    assert run_command(cmd)
    assert cmd1.counter == 1
    assert cmd2.counter == 1
    assert cmd3.counter == 0
    assert cmd4.counter == 1


def test_safety():

    class ElifBeforeIfCommand(CommandGroup):
        def __init__(self):
            super().__init__('Test ELIF before IF')

            @fc.ELIF(lambda: True)
            def do_nothing(self):
                self.addSequential(InstantCommand())

    with pytest.raises(ValueError):
        cmd = ElifBeforeIfCommand()

    class ElseBeforeIfCommand(CommandGroup):
        def __init__(self):
            super().__init__('Test ELSE before IF')

            @fc.ELSE
            def do_nothing(self):
                self.addSequential(InstantCommand())

    with pytest.raises(ValueError):
        cmd = ElseBeforeIfCommand()

    class BreakTooBigCommand(CommandGroup):
        def __init__(self):
            super().__init__('Test BREAK too large')
            self.setRunWhenDisabled(True)

            @fc.WHILE(lambda: True)
            def do_loop(self):
                fc.BREAK(2)

    cmd = BreakTooBigCommand()

    with pytest.raises(ValueError):
        run_command(cmd)

    class BreakWithoutLoop(CommandGroup):
        def __init__(self):
            super().__init__('Test BREAK outside loop')
            self.setRunWhenDisabled(True)

            fc.BREAK()

    with pytest.raises(ValueError):
        cmd = BreakWithoutLoop()

    class BreakAfterLoop(CommandGroup):
        def __init__(self):
            super().__init__('Test BREAK after loop')
            self.setRunWhenDisabled(True)

            x = 5
            def do_loop():
                nonlocal x

                x -= 1

                return x > 0

            @fc.WHILE(do_loop)
            def count_to_four(self):
                self.addSequential(InstantCommand())

            @fc.IF(lambda: True)
            def late_break(self):
                fc.BREAK()

    with pytest.raises(ValueError):
        cmd = BreakAfterLoop()

    with pytest.raises(ValueError):
        fc.RETURN()
