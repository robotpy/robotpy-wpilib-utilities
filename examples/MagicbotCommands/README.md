# Running a library's autonomous command in MagicBot

This hardware-free example demonstrates adapting a command-based autonomous
routine to MagicBot without adopting `CommandScheduler`.

- `external_auto.py`: a standalone `commands2.Command` that drives forward at
  0.5 m/s for one second, then stops. It knows nothing about MagicBot and stands
  in for an autonomous command returned by an external library.
- `components.py`: `AutoCommands` constructs and stores that command, passing a
  callback to the `Drive` component. When asked to start, it calls the injected
  `CommandRunner.run()` once. `Drive` simulates distance instead of using motors.
- `autonomous/drive_forward.py`: the selected autonomous mode asks the component
  to start the command when autonomous is enabled and cancel it on exit,
  including direct transitions to teleop. The runner also interrupts all active
  commands and clears pending requests when the robot is disabled.
- `robot.py`: declares components in execution order: adapter, runner, drivetrain.

From this directory, run `python -m robotpy sim` and enable autonomous with
`Library command` selected. The simulated drivetrain travels about half a meter
and stops. Disable and re-enable autonomous to run the same command again.
Run the simulation test with `python -m robotpy test --builtin`.

This is a lifecycle integration example, not a complete external-library adapter.
The runner initializes, executes, and ends commands, but does not provide
scheduler features such as requirement arbitration or event-trigger scheduling.
External commands that depend on those features need additional integration.
