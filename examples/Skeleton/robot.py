from typing import override

import magicbot


class Robot(magicbot.MagicRobot):
    @override
    def create_objects(self) -> None:
        self.logger.info("Create objects here")

    @override
    def simulation_init(self) -> None:
        pass

    @override
    def robot_periodic(self) -> None:
        super().robot_periodic()

    @override
    def simulation_periodic(self) -> None:
        pass

    @override
    def disabled_init(self) -> None:
        self.logger.info("Start disabled mode")

    @override
    def disabled_periodic(self) -> None:
        pass

    @override
    def autonomous_init(self) -> None:
        self.logger.info("Start autonomous mode")

    @override
    def teleop_init(self) -> None:
        self.logger.info("Start teleop mode")

    @override
    def teleop_periodic(self) -> None:
        pass

    @override
    def utility_init(self) -> None:
        self.logger.info("Start utility mode")

    @override
    def utility_periodic(self) -> None:
        pass
