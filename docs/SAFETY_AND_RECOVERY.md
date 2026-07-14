# Safety and recovery behaviour

## Startup and power recovery

VNH PWM and direction outputs are forced off before communication starts. A board
never resumes a command that was active before reset. After boot it requires valid
configuration, a fresh ARM and a new movement command.

If power fails during travel, position becomes unknown unless a definitive external
position sensor is active. The next movement must home to a known end position under
current, timeout and edge protection. Automatic movement after power restoration is
disabled by default.

## End-stop detection

Internal actuator end switches remove motor current. Firmware accepts this as a valid
end stop only when:

- normal current was observed after startup;
- minimum travel time has elapsed;
- current remains below the calibrated zero threshold for the confirmation interval;
- external position sensors do not contradict the result.

Early loss of current is reported as disconnected actuator, not as a successful end stop.

## Calibration

Opening and closing are calibrated independently. During a full stroke every channel
records the interval from motor start to confirmed current disappearance. The slowest
channel remains at maximum permitted PWM and faster channels are reduced toward the
same total travel time, never below the configured minimum torque PWM.

Only complete, fault-free strokes are eligible for adaptation. Edge activation,
overcurrent, manual stop, sensor conflict or communication loss discards the sample.
Calibration records use CRC and are committed only after a complete pass.

Without individual position feedback this aligns total stroke time, not exact position
at every point. Mechanisms that cannot tolerate transient skew require encoders, Hall
sensors or potentiometers on every actuator.
