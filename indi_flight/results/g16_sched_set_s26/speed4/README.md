# B26 speed 4: G1.6 set with the sim-time player (S26 launch, analysed S27)

15/15 runs flew first attempt (hover, step_roll, traj_lemniscate x5, seed 1, `--sched --sched-anchor`, quad5in, PID).
Command: `indi_flight/bench/g16_sched_set.sh`. Logs untracked; metrics.json, run.json, sched.txt per run.

## Mode instants (`second_key_player.py` per log -> `*/r*/player_key.json`, table `mode_instants.txt`)
- Triggers: arm applied at 30.000000 s in 12/15 runs, 30.001250 s (+1 IMU tick) in 3/15; offboard at 52.000000 s
  in 15/15. G1.6(a1) as proposed in Q3 (trigger within 1 IMU period): met.
- PX4 response after the trigger: arm 1.25-10.0 ms, offboard 11.25-20.0 ms. Spread per scenario: arm 7.5 ms,
  offboard 6.25-8.75 ms. Same as A-17 (Commander phase). Note for Q3 (a2): the spread is within one Commander
  period (10 ms) but the offboard *latency* is 11-20 ms (1-2 ticks), so (a2) must bound the spread, or the latency
  at 2 Commander periods.

## Same-seed spreads (`G16_ROOT=<this dir> bench/g16_spread.py` -> `spread.json`), vs pre-player `det_g16_w125`
- step_roll: much tighter. Step delay spread 15 -> 1.4 ms, settle 19 -> 2.5 ms, attitude RMS 5.6 % -> 0.96 %,
  effort 14 % -> 1.9 %. The step instants now sit on the sim clock (t0 spread 0.89 s -> 7.5 ms).
- traj_lemniscate: about unchanged (truth RMS 1.15 % -> 1.95 %, max dev 9.3 % -> 6.2 %, attitude RMS 0.52 -> 0.23 %).
- hover: wider in relative terms on noise-floor metrics (rate RMS roll 13 -> 77 % relative, 0.0001 -> 0.0009 rad/s
  absolute; position RMS 0.6 -> 1.9 cm). All are at the noise floor (G1.6 note s13); to be judged against G3/G5
  thresholds (G1.6b), not relative.
- **ref_ned[2] spread 2.3 m in hover and traj**: hover r2 and traj r1 hold 7.2 m true altitude instead of 5.0 m.
  Cause: the EKF height is 2.3 m off on the ground before arm (`prearm_zbias.txt`, `bench/prearm_zbias.py`: estimate
  minus truth -0.01 m at 20 s, -2.28 m at 29 s), so take-off goes 2.3 m too high and the EKF converges in the climb.
  This is A-14 in runs logged from boot (`--log-from-start` is the default): A-14 reopened. The same pattern is in the
  pre-player set (det_g16_w125: step_roll r2, r4, traj r4 at -7.2 m). It changes the flown scenario, so it is a
  G1.6(c) item: same-seed runs are not the same flight in 2/15 cases.
