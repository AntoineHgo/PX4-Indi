# G1.6 re-fly, speed 1, S32/S33 (same build and script as speed 4)

15/15 flew (docker_rc 0). Metrics recomputed in S33 with the current `bench/metrics.py` (quat_angle fix). Spreads:
`spread.json` (`G16_ROOT=<this dir> bench/g16_spread.py`), key rows vs speed 4 in `spread_key.txt`.

- Speed factor 1 vs 4: same spreads within a factor ~2 on every key row; no metric is speed-dependent beyond its
  same-seed spread. step_roll delay spread 0.4-1.0 ms (<= 1.5 %), settle 1 IMU period, effort 1.8 %; traj position
  RMS 0.1 %, max dev 0.9 %, attitude 2.2 %.
- hover ref_ned[2] spread 0.086 m (speed 4: 0.135 m): A-14 effect stays gone.
- hover truth attitude spread 0.857 deg (108 %): A-19 EKF heading error, as at speed 4 (`../../a19_s33/README.md`).
- A-20 check (`../a20_check.md`, 30 logs, both speeds): baro_fault 0/30; |bias0| <= 0.18 m in 28/30, 0.72 m in
  speed4 step_roll r4 and traj r5, the two runs with the largest CAL_OFF at start (-9.8, -7.3 Pa ~ 0.6-0.8 m);
  max EKF-truth z error 15-35 s: 0.174 m in 1/30 (speed1 step_roll r5), > 0.1 m in 10/30.
