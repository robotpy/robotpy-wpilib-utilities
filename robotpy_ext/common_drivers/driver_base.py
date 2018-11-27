class DriverBase(object):
    """
    This should be the base class for all drivers in the cdl,
    currently all it does is spit out a warning message if the driver has not been verified.
    """

    #:This should be overloaded by the driver,
    # It is just a mechanism to ensure code quality for device drivers. Upon creation of a new driver,
    # it will be either left alone, or overloaded to be False. Once the functionality of the driver is verified,
    # this will get overloaded to true by whoever verifies it.
    verified = False

    def __init__(self):
        """
        Constructor for DriverBase, all this does is print a message to console if the driver has not been verified yet.
        """
        if not self.verified:
            print(
                "Warning, device driver {} has not been verified yet, please use with caution!".format(
                    self.__class__.__name__
                )
            )
