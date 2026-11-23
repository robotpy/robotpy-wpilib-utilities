# MagicBot Simple

Imported from the archived [robotpy/examples](https://github.com/robotpy/examples/tree/70cfcfc3965229309c3b0b6264e1789225d080b0/MagicbotSimple)
repository at commit `70cfcfc3965229309c3b0b6264e1789225d080b0`.

Demonstrates component injection, constant injection, feedback, per-cycle reset
values, and a two-state autonomous routine. Hold joystick 0's trigger to run the
motor on PWM 2 in teleop. Autonomous waits two seconds, runs that motor for five
seconds, then stops.

Updated for the 2027 snake_case WPILib and MagicBot APIs. The removed Talon class
is replaced with a PWMMotorController subclass using Talon PWM bounds. Adjust
these bounds if using a different motor controller.

With this repository installed (`python -m pip install -e .`) and compatible
WPILib, robotpy-cli, pytest, and pytest-reraise installed, run from this directory:

```sh
python -m robotpy test
```

Tests exercise all robot modes and check injection, autonomous timing, and motor
reset behavior. The imported source retains its upstream copyright notices.
