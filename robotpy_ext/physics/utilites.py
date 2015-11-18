import math


def update_gyro(hal_data, gyro_channel, angle):
    """
    A utility function to update a gyro in hal_data.

    :param hal_data: The hal_data dictionary
    :param gyro_channel: The analog channel to simulate a gyro on.
    :param angle: The angle, in radians, to set the gyro to.
    """

    # XXX: for now, use a constant to compute the output voltage
    #      .. however, we should do the actual calculation at some point?

    hal_data['analog_in'][gyro_channel]['accumulator_value'] = math.degrees(angle) / 2.7901785714285715e-12
