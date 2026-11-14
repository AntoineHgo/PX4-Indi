# THR_MDL_FAC for the gz x500 (session 32, consistency requirement of D-omega2)

PX4 applies THR_MDL_FAC in the output mixer (`src/lib/mixer_module/functions/FunctionMotors.hpp`,
`updateValues`), after `actuator_motors`: output x solves u = f x^2 + (1 - f) x, where u is the allocator's
normalised thrust. The gz x500 maps the output to rotor speed linearly, omega = 150 + 850 x rad/s (SDF
SIM_GZ_EC_MIN/MAX; confirmed from logs in s31: x 0.728 -> 769 rad/s), so the realised normalised thrust is
T = (omega/1000)^2 = (0.15 + 0.85 x)^2.

Least-squares fit of f over x in [0.4, 1]: **f = 0.683**.

| THR_MDL_FAC | hover u | realised T at hover | local dT/du at hover | max abs(T - u), u in [0.2, 1] |
|---|---|---|---|---|
| 0 (v1, v2 so far) | 0.727 | 0.590 | 1.306 | 0.170 |
| 0.683 | 0.592 | 0.590 | 0.996 | 0.005 |

With 0.683 the allocator's u equals (omega/omega_max)^2 to 0.005, which is what the v2 INDI (D-omega2) needs
to put its measured state and its increments in the same space. It is a vehicle characterisation, so it goes
into the v2 config for BOTH controllers (`bench/params/v2_fac.params` = DNF + FAC). Effect on PID: its
torque-to-thrust gain at hover drops by 1/1.306 = 0.77x, so the v2 PID tuning check (r1/r2, flown with FAC 0)
must be repeated on the FAC config before any v2 comparison. Computed from the SDF curve (no flight); the
hover-u prediction 0.592 is checked by the first FAC flight (actuator_motors median in hover).
