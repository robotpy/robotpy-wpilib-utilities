import hal

from wpilib.iterativerobot import IterativeRobot
from wpilib.command.scheduler import Scheduler
from wpilib.livewindow import LiveWindow


class CommandBasedRobot(IterativeRobot):
    '''
    The base class for a Command-Based Robot. To use, instantiate commands and
    trigger them.
    '''

    def startCompetition(self):
        """
        Provide an alternate "main loop" via startCompetition(). Rewritten
        from IterativeRobot for readability and to initialize scheduler.
        """

        hal.report(hal.HALUsageReporting.kResourceType_Framework,
                   hal.HALUsageReporting.kFramework_Iterative)

        self.scheduler = Scheduler.getInstance()
        self.robotInit()

        # Tell the DS that the robot is ready to be enabled
        hal.observeUserProgramStarting()

        # loop forever, calling the appropriate mode-dependent function
        while True:
            if self.ds.isDisabled():
                hal.observeUserProgramDisabled()
                self.disabledInit()
                while self.ds.isDisabled():
                    self.disabledPeriodic()
                    self.ds.waitForData()

            elif self.ds.isAutonomous():
                hal.observeUserProgramAutonomous()
                self.autonomousInit()
                while self.ds.isEnabled() and self.ds.isAutonomous():
                    self.autonomousPeriodic()
                    self.ds.waitForData()

            elif self.ds.isTest():
                hal.observeUserProgramTest()
                LiveWindow.setEnabled(True)

                self.testInit()
                while self.ds.isEnabled() and self.ds.isTest():
                    self.testPeriodic()
                    self.ds.waitForData()

                LiveWindow.setEnabled(False)

            else:
                hal.observeUserProgramTeleop()
                self.teleopInit()
                # isOperatorControl checks "not autonomous or test", so we need
                # to check isEnabled as well, since otherwise it will continue
                # looping while disabled.
                while self.ds.isEnabled() and self.ds.isOperatorControl():
                    self.teleopPeriodic()
                    self.ds.waitForData()


    def commandPeriodic(self):
        '''
        Run the scheduler regularly. If an error occurs during a competition,
        prevent it from crashing the program.
        '''

        try:
            self.scheduler.run()
        except Exception as error:
            if not self.ds.isFMSAttached():
                raise

            '''Just to be safe, stop all running commands.'''
            self.scheduler.removeAll()

            self.handleCrash(error)


    autonomousPeriodic = commandPeriodic
    teleopPeriodic = commandPeriodic
    disabledPeriodic = commandPeriodic


    def testPeriodic(self):
        '''
        Test mode will not run normal commands, but motors can be controlled
        and sensors viewed with the SmartDashboard.
        '''

        LiveWindow.run()


    def handleCrash(self, error):
        '''
        Called if an exception is raised in the Scheduler during a competition.
        Writes an error message to the driver station by default. If you want
        more complex behavior, override this method in your robot class.
        '''

        self.ds.reportError(str(error), printTrace=True)
