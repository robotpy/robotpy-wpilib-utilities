#----------------------------------------------------------------------------
# Copyright (c) Kauai Labs 2015. All Rights Reserved.
#
# Created in support of Team 2465 (Kauaibots).  Go Purple Wave!
#
# Open Source Software - may be modified and shared by FRC teams. Any
# modifications to this code must be accompanied by the \License.txt file
# in the root directory of the project
#----------------------------------------------------------------------------

import enum

__all__ = ['getNavxDigitalChannel',
           'getNavxPWMChannel',
           'getNavxAnalogInChannel',
           'getNavxAnalogOutChannel',
           'getChannelFromPin',
           'PinType']

MAX_NAVX_MXP_DIGIO_PIN_NUMBER      = 9
MAX_NAVX_MXP_ANALOGIN_PIN_NUMBER   = 3
MAX_NAVX_MXP_ANALOGOUT_PIN_NUMBER  = 1
NUM_ROBORIO_ONBOARD_DIGIO_PINS     = 10
NUM_ROBORIO_ONBOARD_PWM_PINS       = 10
NUM_ROBORIO_ONBOARD_ANALOGIN_PINS  = 4
NUM_ROBORIO_ONBOARD_ANALOGOUT_PINS = 2


def getNavxDigitalChannel(pin):
    """Get the WPILib channel number for a digital input on a NavX MXP
    
    :param pin: The NavX pin number (0-9)
    :type pin: int
    
    :returns: RoboRIO channel number
    """
    if pin < 0 or pin > MAX_NAVX_MXP_DIGIO_PIN_NUMBER:
        raise ValueError("Invalid navX MXP Digital I/O pin number")
    
    return pin + NUM_ROBORIO_ONBOARD_DIGIO_PINS + (4 if pin > 3 else 0);
    
def getNavxPWMChannel(pin):
    """Get the WPILib channel number for a PWM on a NavX MXP
    
    :param pin: The NavX pin number (0-9)
    :type pin: int
    
    :returns: RoboRIO channel number
    """
    if pin < 0 or pin > MAX_NAVX_MXP_DIGIO_PIN_NUMBER:
        raise ValueError("Invalid navX MXP PWM pin number")
    
    return pin + NUM_ROBORIO_ONBOARD_PWM_PINS
    
def getNavxAnalogInChannel(pin):
    """Get the WPILib channel number for an Analog Input on a NavX MXP
    
    :param pin: The NavX pin number (0-3)
    :type pin: int
    
    :returns: RoboRIO channel number
    """
    if pin < 0 or pin > MAX_NAVX_MXP_ANALOGIN_PIN_NUMBER:
        raise ValueError("Invalid navX MXP Analog In pin number")
    
    return pin + NUM_ROBORIO_ONBOARD_ANALOGIN_PINS
    
def getNavxAnalogOutChannel(pin):
    """Get the WPILib channel number for an Analog Output on a NavX MXP
    
    :param pin: The NavX pin number (0-1)
    :type pin: int
    
    :returns: RoboRIO channel number
    """
    if pin < 0 or pin > MAX_NAVX_MXP_ANALOGOUT_PIN_NUMBER:
        raise ValueError("Invalid navX MXP Analog Out pin number")
    
    return pin


class PinType(enum.Enum):
    DigitalIO = 1
    PWM = 2
    AnalogIn = 3
    AnalogOut = 4


def getChannelFromPin(pinType, pin):
    """Converts from a NavX MXP pin type and number to the corresponding
    RoboRIO channel number that is used by WPILib.
    
    :param pinType: The type of pin to convert 
    :type pinType: :class:`PinType`
    :param pin: 
    :type pin: int
    
    :returns: RoboRIO channel number
    """
    
    if pinType == PinType.DigitalIO:
        return getNavxDigitalChannel(pin)
    
    if pinType == PinType.PWM:
        return getNavxPWMChannel(pin)
    
    if pinType == PinType.AnalogIn:
        return getNavxAnalogInChannel(pin)
    
    if pinType == PinType.AnalogOut:
        return getNavxAnalogOutChannel(pin)
    
    raise ValueError("Invalid pin type specified")
