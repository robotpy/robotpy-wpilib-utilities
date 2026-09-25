import magicbot


class Robot(magicbot.MagicRobot):
    def create_objects(self) -> None:
        self.logger.info("Create objects here")

    def simulation_init(self) -> None:
        pass

    def robot_periodic(self) -> None:
        super().robot_periodic()

    def simulation_periodic(self) -> None:
        pass

    def disabled_init(self) -> None:
        self.logger.info("Start disabled mode")

    def disabled_periodic(self) -> None:
        pass

    def autonomous_init(self) -> None:
        self.logger.info("Start autonomous mode")

    def teleop_init(self) -> None:
        self.logger.info("Start teleop mode")

    def teleop_periodic(self) -> None:
        pass

    def utility_init(self) -> None:
        self.logger.info("Start utility mode")

    def utility_periodic(self) -> None:
        pass
