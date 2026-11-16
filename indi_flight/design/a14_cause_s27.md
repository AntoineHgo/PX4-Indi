# A-14 cause, session 27 (EKF2 height jump on the ground before arm)

Evidence: `bench/a14_compare.py` (log time = sim time, arm at 30.0 s) on
`results/g16_sched_set_s26/speed4/`: BAD hover/r2, BAD traj_lemniscate/r1, GOOD hover/r1 (+ r3-r5, step_roll, traj r2-r5 summary).

## Mechanism (EKF2 behaviour, triggered by the sim baro; not a GNSS step)
- The error is not a step, it is a 2.2 s ramp. hover r2, err = z_est - z_truth:
  -0.01 m at 21.5 s, -0.34 at 22.0, -0.73 at 22.5, -1.06 at 23.0, -1.55 at 24.1,
  -1.83 at 25, -2.28 at 29. First |err| > 0.5 m at 22.21 s. Plateau, no later correction.
- First signal to change: `cs_baro_hgt` 0 -> 1 at 21.364 s (baro height fusion start) in r2.
  Good runs do the same (r3 21.38, r4 21.35, r5 21.21, ...). Nothing else flips
  (cs_gps_hgt = 1 all along, no z reset: z_reset_counter 2, delta_z const, ref_alt const 488.03).
  GNSS height obs stays -488.0..-488.08 throughout (no GNSS jump). vehicle_air_data baro_alt_meter
  488.1-488.7 in r2 (no baro step either; raw baro agrees with GNSS to < 1 m).
- The baro observation carries a large bias term from `estimator_baro_bias` (EKF2 BiasEstimator):
  obs ~ -raw + bias (-488 + -30.3 = -518 in good r1; -488 + -14.7 = -503 in bad r2).
  - GOOD r1: bias settles to -30.3 (21.5 s onward); baro innovation 29.8 m, test_ratio 2.9 > 1,
    rejected (fused=0). After 5 s of continuous rejection `cs_baro_fault` 0->1 and `cs_baro_hgt`
    1->0 (r1 26.52, r3 26.45, r4 26.39, r5 26.27 s). Baro is dropped; height stays on GNSS.
  - BAD r2: bias is -123.86 at 20.37 s (innov 0), then jumps to -14.7 by ~21.4 s. Innovation 15.1 m at
    22.0 s, test_ratio 0.73 < 1 (innov var 12.35, gate EKF2_BARO_GATE 5), so fused=1, rej=0 from 21.51 s on.
    BAD lemniscate r1: bias -124.3 -> -15.2, ratio 0.70 at 22.0 s, same. baro_fault never sets (0 in 21-35 s).
  - The persistent ~14 m baro innovation is fused against GNSS; the equilibrium pull on EKF z is -2.28 m
    (up; r2) / -2.32 m (r1 traj). Accel bias z state also moves 0.007 -> 0.033 m/s^2 in r2 (side effect).
- Score: 2/15 runs bad, both are the ones where baro bias landed at ~-15 instead of ~-30, i.e. inside the 5-sigma gate.
  Take-off then holds 2.3 m high in truth (7.2 vs 5.0 m) because the controller tracks the EKF z.

## Unverified
- Why the bias estimator output is non-physical (-30, -124, -15 m) while the raw baro is consistent
  with GNSS, and what makes it settle differently run to run (same seed; sim baro noise/sample timing?).
  Suspect: the baro bias state is initialised/reset from a baro sample or offset (sensor_baro pressure in the
  log is ~101320 Pa, sea-level, whereas vehicle_air_data pressure is ~95600 Pa; this mismatch is not explained).
- I did not read EKF2 source; the obs = -raw + bias form is inferred from numbers (two runs, +-1 m).
- EKF2_HGT_REF value not read from the logs (cs_gps_hgt = 1 so GNSS is the active reference).
- The sim baro stream itself between 20 and 21.5 s was not compared bit-for-bit across runs.

## Closing test
Same-seed repeat (>= 15 hover runs, `-f`, speed 4, scenario unchanged) with EKF2_BARO_CTRL=0 (parameter in the
bench/SITL param set, no EKF2 edit). Pass: cs_baro_hgt = 0 for the whole log, max |z_est - z_truth| < 0.1 m
in 15-35 s on all runs, true hold altitude 5.0 m +- 0.05 on all runs. Also check ref_alt/estimator_baro_bias
are absent or unused. Cheap cause test beforehand: replay the current 15-run pairing with `a14_compare.py` to see
that all 13 good runs show baro_fault at ~26.2-26.5 s and both bad ones none (done: confirmed above).

## Fix candidate (no EKF2 / stock module change)
Set `EKF2_BARO_CTRL 0` for the INDI SITL bench (GNSS height only; sim has GNSS, baro adds nothing to the
metrics, which use truth). Weaker alternative: `EKF2_BARO_GATE` 2-3 so the -15 m case is rejected as well
(test_ratio scales 1/gate^2: 0.7 at gate 5 -> 1.9 at gate 3), still dependent on the bias state. Bench-only
backstop: player arms only when |z_est - z_truth| < 0.1 m (already listed in A-14 NEXT).
Hardware flight with a real baro is a separate question: this is a sim-baro artefact until shown otherwise.
