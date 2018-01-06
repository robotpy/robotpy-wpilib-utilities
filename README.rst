robotpy-wpilib-utilities
========================

.. image:: https://travis-ci.org/robotpy/robotpy-wpilib-utilities.svg
    :target: https://travis-ci.org/robotpy/robotpy-wpilib-utilities

Useful utility functions/objects for RobotPy WPILib (2015+).

Documentation
-------------

* API Documentation can be found at http://robotpy-wpilib-utilities.readthedocs.io
* Example programs can be found at https://github.com/robotpy/examples

Contribution guidelines
-----------------------

This repository is intended to be a common place for high quality code to live
for "things that should be in WPILib, but aren't". The python implementation of
WPILib is intended to be very close to the implementations in the other languages,
which is where packages like this come in.

* Most anything will be accepted, but ideally full frameworks will be separate
  packages and don't belong here
* Ideally, contributions will have unit tests
* Ideally, contributions will not have external python dependencies other than
  WPILib -- though, this may change.
* Contributions will work (or at least, not break) on all supported RobotPy
  platforms (Windows/Linux/OSX, RoboRio)
* All pull requests will be tested using Travis-CI

Installation
------------

This library is automatically installed when you install pyfrc or RobotPy

License
-------

BSD License, similar to WPILib.

Authors
-------

- Dustin Spicuzza (dustin@virtualroadside.com)
- Tim Winters (twinters@wpi.edu)
- David Vo (@auscompgeek)
- Insert your name here!
