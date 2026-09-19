import magicbot


class Robot(magicbot.MagicRobot):
    def createObjects(self) -> None:
        self.logger.info("Create objects here")

    def robotPeriodic(self) -> None:
        super().robotPeriodic()

    def disabledInit(self) -> None:
        self.logger.info("Start disabled mode")

    def disabledPeriodic(self) -> None:
        pass

    def autonomousInit(self) -> None:
        self.logger.info("Start autonomous mode")

    def teleopInit(self) -> None:
        self.logger.info("Start teleop mode")

    def teleopPeriodic(self) -> None:
        pass

    def testInit(self) -> None:
        self.logger.info("Start utility mode")

    def testPeriodic(self) -> None:
        pass
