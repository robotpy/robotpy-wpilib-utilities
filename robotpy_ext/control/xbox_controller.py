
import hal
import wpilib

class XboxController:
    '''
        Allows usage of an Xbox controller, with sensible names for xbox
        specific buttons and axes.
    
        Mapping based on http://www.team358.org/files/programming/ControlSystem2015-2019/images/XBoxControlMapping.jpg
    '''
    
    def __init__(self, port):
        '''
        :param port: The port on the driver station that the controller is
            plugged into.
        :type  port: int
        '''
    
        self.ds = wpilib.DriverStation.getInstance()
        self.port = port
        
        hal.HALReport(hal.HALUsageReporting.kResourceType_Joystick, port)
    
    def getLeftX(self):
        """Get the left stick X axis
        
        :returns: -1 to 1
        :rtype: float
        """
        return self.ds.getStickAxis(self.port, 0)
    
    def getLeftY(self):
        """Get the left stick Y axis
        
        :returns: -1 to 1
        :rtype: float
        """
        return self.ds.getStickAxis(self.port, 1)
    
    getX = getLeftX
    getY = getLeftY
    
    def getLeftPressed(self):
        """Determines if the left stick is pressed
        
        :returns: True if pressed, False otherwise
        :rtype: bool
        """
        return self.ds.getStickButton(self.port, 8)
    
    def getPOV(self):
        """Get the state of a POV on the joystick.

        :param pov: which POV (default is 0)
        :type  pov: int
        :returns: The angle of the POV in degrees, or -1 if the POV is not
                  pressed.
        :rtype: float
        """
        return self.ds.getStickPOV(self.port, 0)
    
    def getRightX(self):
        """Get the right stick X axis
        
        :returns: -1 to 1
        :rtype: float
        """
        return self.ds.getStickAxis(self.port, 4)
    
    def getRightY(self):
        """Get the right stick Y axis
        
        :returns: -1 to 1
        :rtype: float
        """
        return self.ds.getStickAxis(self.port, 5)
    
    def getRightPressed(self):
        """Determines if the right stick is pressed
        
        :returns: True if pressed, False otherwise
        :rtype: bool
        """
        return self.ds.getStickButton(self.port, 9)
    
    def getButtonA(self):
        """Gets whether the A button is pressed
        
        :returns: True if pressed, False otherwise
        :rtype: bool
        """
        return self.ds.getStickButton(self.port, 0)
    
    def getButtonB(self):
        """Gets whether the B button is pressed
        
        :returns: True if pressed, False otherwise
        :rtype: bool
        """
        return self.ds.getStickButton(self.port, 1)
    
    def getButtonX(self):
        """Gets whether the X button is pressed
        
        :returns: True if pressed, False otherwise
        :rtype: bool
        """
        return self.ds.getStickButton(self.port, 2)
    
    def getButtonY(self):
        """Gets whether the X button is pressed
        
        :returns: True if pressed, False otherwise
        :rtype: bool
        """
        return self.ds.getStickButton(self.port, 3)
    
    def getStart(self):
        """Gets whether the Start button is pressed
        
        :returns: True if pressed, False otherwise
        :rtype: bool
        """
        return self.ds.getStickButton(self.port, 7)
    
    def getBack(self):
        """Gets whether the Back button is pressed
        
        :returns: True if pressed, False otherwise
        :rtype: bool
        """
        return self.ds.getStickButton(self.port, 6)
    
    def getLeftBumper(self):
        """Gets whether the left bumper is pressed
        
        :returns: True if pressed, False otherwise
        :rtype: bool
        """
        return self.ds.getStickButton(self.port, 4)
    
    def getRightBumper(self):
        """Gets whether the right bumper is pressed
        
        :returns: True if pressed, False otherwise
        :rtype: bool
        """
        return self.ds.getStickButton(self.port, 5)
    
    def getLeftTrigger(self):
        """Gets whether the left trigger is pressed
        
        :returns: True if pressed, False otherwise
        :rtype: bool
        """
        return self.ds.getStickAxis(self.port, 2) > 0
    
    def getRightTrigger(self):
        """Gets whether the right trigger is pressed
        
        :returns: True if pressed, False otherwise
        :rtype: bool
        """
        return self.ds.getStickAxis(self.port, 3) > 0


