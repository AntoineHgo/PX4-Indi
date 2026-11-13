# G1 / actuator identification v0 (session 5, 2026-11-13)

Script: `bench/identify_g1.py` (least squares on increments of
`xyz_derivative` vs `H(A(torque_sp))`, grid over actuator tc and integer
delay). Data: PID default, seed1 of `step_roll` and `rate_step_roll`
(speed 1), 22 668 in-flight samples at 250 Hz.

| axis | G1 (rad/s^2 per unit torque) | tc (s) | delay (samples) | R^2 |
|------|------|------|------|------|
| roll | 321 | 0.025 | 1 | 0.63 |
| pitch | 416 | 0.005 | 1 | 0.37 |
| yaw | 31 | 0.005 | 0 | 0.002 |

Interpretation:
- Roll is the only axis excited by these logs; its fit is usable as a
  starting value (G1_r ~ 320, tc 0.025 = the x500 spin-down constant,
  1 sample = the zero-order hold between torque publication and the next
  gyro sample). R^2 0.63: noise and the thrust ~ omega^2 nonlinearity
  remain unexplained.
- Pitch and yaw values are NOT identified (no excitation): need
  `step_pitch` and `step_yaw` runs (or a dedicated chirp/doublet scenario).
  By symmetry of the x500 (Ixx = Iyy) expect G1_p ~ G1_r.
- Not yet cross-checked against the model value M_max/Ixx with the
  allocator normalisation; do that before tuning.
