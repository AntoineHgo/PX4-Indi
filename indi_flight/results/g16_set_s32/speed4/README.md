# G1.6 re-fly, speed 4, S32 (baro elevation fix 4443079c0b + A-20 atomic ref 4297ba9869)

Script `bench/g16_set_s32.sh`; pretest hover PASS on the A-14 mechanism (`../pretest/check.md`: bias0 0.12 m,
baro_fault 0, hold -5.008 m; EKF-truth z 0.136 m, inside the parked 0.15 m bound). 15/15 runs flew (docker_rc 0).
Metrics re-computed after the batch with the current `bench/metrics.py` (quat_angle fix, S32) for every run, so the
set uses one metric version. Spreads: `spread.json` (`G16_ROOT=<this dir> bench/g16_spread.py`), key rows in
`spread_key.txt` (vs B26 speed 4 before the baro fixes).

- A-14 effect on the flown scenario GONE: hover ref_ned[2] spread 2.31 -> 0.135 m, traj 2.32 -> 0.097 m, step 0.108 m.
- step_roll: delay spread 0.9-1.1 ms (1.4-1.7 %), settle 0.4-1.2 %, effort 2.5 %, attitude 1.5 %: as B26.
- traj: truth max dev 4.7 %, position RMS 0.9 %, effort 0.2 %, attitude 3.0 % (yaw, see below).
- hover: noise-floor metrics wide in relative terms (rate roll 0.0004 rad/s abs, position RMS 8 mm abs).
- **hover truth attitude spread 0.925 deg (93 %) = EKF heading error, A-19 REOPENED**: truth-minus-EKF yaw mean
  -0.94/-1.54/-0.66/-0.59/-1.21 deg (r1..r5); the yaw setpoint follows the EKF. Exceeds the 1.1 deg bound set in S32
  from the 10 B26 logs. Same seed, so the EKF heading itself is not deterministic run to run: G1.6(c) item.
