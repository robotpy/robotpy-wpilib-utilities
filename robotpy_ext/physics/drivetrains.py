import math

'''
    Based on input from various drive motors, these helper functions
    simulate moving the robot in various ways. Many thanks to
    `Ether <http://www.chiefdelphi.com/forums/member.php?u=34863>`_
    for assistance with the motion equations.
      
    When specifying the robot speed to the below functions, the following
    may help you determine the approximate speed of your robot:
    
    * Slow: 4ft/s
    * Typical: 5 to 7ft/s
    * Fast: 8 to 12ft/s
        
    Obviously, to get the best simulation results, you should try to
    estimate the speed of your robot accurately.
'''

    
def two_motor_drivetrain(last_state, dt, l_motor, r_motor, x_wheelbase=2, speed=5):
    '''
        Two center-mounted motors with a simple drivetrain. The 
        motion equations are as follows::
    
            FWD = (L+R)/2
            RCW = (L-R)/W
        
        * L is forward speed of the left wheel(s), all in sync
        * R is forward speed of the right wheel(s), all in sync
        * W is wheelbase in feet
        
        If you called "SetInvertedMotor" on any of your motors in RobotDrive,
        then you will need to multiply that motor's value by -1.
        
        .. note:: WPILib RobotDrive assumes that to make the robot go forward,
                  the left motor must be set to -1, and the right to +1 

        :param last_state: The state dictionary containing position and velocity data from the last iteration.
        :param dt:         The time elapsed since the last iteration.
        :param l_motor:    Left motor value (-1 to 1); -1 is forward
        :param r_motor:    Right motor value (-1 to 1); 1 is forward
        :param x_wheelbase: The distance in feet between right and left wheels.
        :param speed:      Speed of robot in feet per second (see above)
        
        :returns: speed of robot (ft/s), clockwise rotation of robot (radians/s)
    '''
    return four_motor_drivetrain(last_state, dt, l_motor, r_motor, l_motor, r_motor, x_wheelbase, speed)


def four_motor_drivetrain(last_state, dt, lr_motor, rr_motor, lf_motor, rf_motor, x_wheelbase=2, speed=5):
    '''
        Four motors, each side chained together. The motion equations are
        as follows::
    
            FWD = (L+R)/2
            RCW = (L-R)/W
        
        * L is forward speed of the left wheel(s), all in sync
        * R is forward speed of the right wheel(s), all in sync
        * W is wheelbase in feet
        
        If you called "SetInvertedMotor" on any of your motors in RobotDrive,
        then you will need to multiply that motor's value by -1.
        
        .. note:: WPILib RobotDrive assumes that to make the robot go forward,
                  the left motors must be set to -1, and the right to +1

        :param last_state: The state dictionary containing position and velocity data from the last iteration.
        :param dt:         The time elapsed since the last iteration.
        :param lr_motor:   Left rear motor value (-1 to 1); -1 is forward
        :param rr_motor:   Right rear motor value (-1 to 1); 1 is forward
        :param lf_motor:   Left front motor value (-1 to 1); -1 is forward
        :param rf_motor:   Right front motor value (-1 to 1); 1 is forward
        :param x_wheelbase: The distance in feet between right and left wheels.
        :param speed:      Speed of robot in feet per second (see above)
        
        :returns: speed of robot (ft/s), clockwise rotation of robot (radians/s)
    '''
    
    l = (lf_motor + lr_motor) * 0.5 * speed
    r = -(rf_motor + rr_motor) * 0.5 * speed

    last_position = last_state["position"]
    last_velocity = last_state["velocity"]

    # Get average angle
    rotation_vel = (r - l) / float(x_wheelbase)
    avg_theta = last_position[2] + rotation_vel*dt/2

    # Calculate new velocity from average rotation
    forward_vel = (r + l) * 0.5
    new_velocity = [
        -math.sin(avg_theta)*forward_vel,
        math.cos(avg_theta)*forward_vel,
        rotation_vel
    ]
    avg_velocity = [(a + b)/2 for a, b in zip(last_velocity, new_velocity)]

    # Integrate new position from average velocity
    new_position = [pos + vel*dt for pos, vel in zip(last_position, avg_velocity)]
    return {
        "position": new_position,
        "velocity": new_velocity
    }


def mecanum_drivetrain(last_state, dt, lr_motor, rr_motor, lf_motor, rf_motor, x_wheelbase=2, y_wheelbase=3, speed=5):
    '''
        Four motors, each with a mecanum wheel attached to it.
        
        If you called "SetInvertedMotor" on any of your motors in RobotDrive,
        then you will need to multiply that motor's value by -1.
        
        .. note:: WPILib RobotDrive assumes that to make the robot go forward,
                  all motors are set to +1

        :param last_state: The state dictionary containing position and velocity data from the last iteration.
        :param dt:         The time elapsed since the last iteration.
        :param lr_motor:   Left rear motor value (-1 to 1); 1 is forward
        :param rr_motor:   Right rear motor value (-1 to 1); 1 is forward
        :param lf_motor:   Left front motor value (-1 to 1); 1 is forward
        :param rf_motor:   Right front motor value (-1 to 1); 1 is forward
        :param x_wheelbase: The distance in feet between right and left wheels.
        :param y_wheelbase: The distance in feet between forward and rear wheels.
        :param speed:      Speed of robot in feet per second (see above)
        
        :returns: Speed of robot in x (ft/s), Speed of robot in y (ft/s), 
                  clockwise rotation of robot (radians/s)
    '''

    #
    # From http://www.chiefdelphi.com/media/papers/download/2722 pp7-9
    # [F] [omega](r) = [V]
    #
    # F is
    # .25  .25  .25 .25
    # -.25 .25 -.25 .25
    # -.25k -.25k .25k .25k
    #
    # omega is
    # [lf lr rr rf]

    last_position = last_state["position"]
    last_velocity = last_state["velocity"]

    # Calculate speed of each wheel
    lr = lr_motor * speed
    rr = rr_motor * speed
    lf = lf_motor * speed
    rf = rf_motor * speed

    # Calculate rotational velocity
    k = abs(x_wheelbase/2) + abs(y_wheelbase/2)
    rotation_vel = (.25/k) * (lf + lr + -rr + -rf)
    avg_theta = last_position[2] + rotation_vel*dt/2

    # Calculate resulting motion
    forward_vel = .25 * (lf + lr + rr + rf)
    strafe_vel = .25 * (lf + -lr + rr + -rf)

    # Rotate to new world velocity
    new_velocity = [
        math.cos(avg_theta)*strafe_vel - math.sin(avg_theta)*forward_vel,
        math.cos(avg_theta)*forward_vel + math.sin(avg_theta)*strafe_vel,
        rotation_vel
    ]
    avg_velocity = [(a + b)/2 for a, b in zip(last_velocity, new_velocity)]

    # Integrate new position from average velocity
    new_position = [pos + vel*dt for pos, vel in zip(last_position, avg_velocity)]
    return {
        "position": new_position,
        "velocity": new_velocity
    }
    

# TODO: swerve drive, etc
