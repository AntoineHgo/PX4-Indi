# Gates: exact tests and thresholds

Written before the first test of each gate and committed. After a gate's first test its thresholds change only to
fix a defect in the test, logged below the gate with date and reason. Starting values are the owner's (MISSION.md);
any tightening or change is justified in `DECISIONS.md`. PID flies the same tests as a reference, never as a pass
condition (F-5). All tests on the reference airframe (F-3) unless stated.

## G1 Evidence integrity (draft 2026-11-15, not yet tested)

Each item is one command (`indi_flight/bench/gate_g1.sh <item>`, to be written) and a pass rule.

| item | test | pass |
|---|---|---|
| G1.1 log rates | parse a nominal flight; for every topic an analysis script declares it needs, compare logged median sample period with the declared rate | every declared topic logged at >= the declared rate, max gap < 3 declared periods outside the start-up second |
| G1.2 ground truth | ground-truth pose carries the simulator's own pose time stamp (sim time), not reception time; check against a scripted constant-velocity truth segment | stamp offset vs sim time < 1 physics step; tracking metrics read truth, not the EKF |
| G1.3 two keys | every primary metric computed by two independently written scripts from the same raw logs | agreement within 1 % relative or 1 mm / 0.1 deg / 0.1 % FS absolute, whichever is larger, on the G1 sample set (>= 5 logs spanning hover, steps, trajectory, disturbance) |
| G1.4 self-tests | every metric and identification script has a synthetic test with a known answer, including one closed-loop case for each identification script | all pass in the bench test runner; each test checked once to fail when the script is broken (lesson 20) |
| G1.5 injectors and variants | each injector and plant variant flown once with the effect measured on the simulator side: frame (body vs world), units, application time in sim time vs commanded, effect on the measured rotor speed | frame and sign correct; magnitude within 2 %; applied time within 1 physics step of commanded and logged as applied |
| G1.6 determinism | same seed, plant and scenario flown 5 times at speed factor 1 and 5 times at the batch speed factor; hover, one step scenario, one trajectory; mode instants checked in the ULog (not the runner's HEARTBEAT view) | (a) PX4 mode transitions within 2 IMU periods across runs; (b) for every primary metric, same-seed spread (max-min) <= max(10 % of the threshold of the gate that uses it, the G1.3 absolute floor); (c) the cause of any remaining run-to-run difference is identified and its bound stated; (d) rule for every later verdict: a metric passes or separates two configurations only if its distance to the threshold (or the difference) exceeds the measured same-seed spread |

G1.1 declared-rate fix (2026-11-16, s20, test defect): the declared rates were a stale copy of the 4 ms world config, not the analysis need. Now: truth topics (position, attitude, angular velocity) at the controller rate (they score rate/attitude tracking); vehicle_local_position 88 Hz (EKF2 output 800/9 Hz on the 1.25 ms world, cause in `design/t39_g1_fixes_s20.md`; position estimator error is a separate metric, not a tracking score). Gap rule unchanged; truth rows FAIL on it (A-15).
G1.6 change before first test (2026-11-15, s13): relative 2 % target replaced by (a)-(d). Reason: hover metrics sit at the noise floor (max deviation 3-4 cm, attitude RMS 0.03 deg), where a relative spread is ill-conditioned (`design/determinism_s12.md`, `design/determinism_s13.md`). See DECISIONS.md D-G1.6.

G1 provisional verdicts (2026-11-16, s27, route check 27 item 1). PROVISIONAL: they assume the recommended option
of owner questions Q2 (A) and Q3 (A); no item is marked passed until the owner answers; reopened if the owner picks B or C.
Thresholds unchanged.
- G1.1 under Q2-A: (i) logger completeness sim_ground_truth 56578 vs gyro 56586 samples (-0.014 %, limit 0.1 %): met;
  (ii) sim holes 7 in 56586 steps (0.012 %, limit 0.05 %), single holes 5.0-6.3 ms (limit 10 ms): met (S24 numbers,
  hover speed 4; re-measure on the final G1 command).
- G1.6 under Q3-A (evidence `results/g16_sched_set_s26/speed4/README.md`; speed 1 pending): (a1) triggers at the same
  sim time within 1 IMU period: met (0 or +1250 us, 15/15). (a2) PX4 response spread 6.25-8.75 ms: within one
  Commander period; latency 1.25-10 ms (arm) and 11.25-20 ms (offboard), so the response is bounded at 2 Commander
  periods, not 1. (b) spreads recorded in `spread.json` (step_roll tighter than pre-player by 3-10x on timing
  metrics). (c) NOT MET: in 2/15 runs the EKF height is 2.3 m off before arm (A-14 reopened), so the flown hover
  altitude differs; cause not identified. (d) in force.

G1.6 verdict (2026-11-15, s17, evidence `results/det_g16_s4/`, `results/det_g16_s1/`, `results/det_g16_w125/README.md`,
second key `results/second_key_window_s15.md`): (a) NOT MET: mode-instant spread 7.5-11 ms on the 1.25 ms world
(threshold 2 IMU periods = 2.5 ms), 12-16 ms on the 4 ms world. (b) open until the G3/G5 thresholds exist; the
spreads are recorded in `spread.json` per batch. (c) MET: cause = mode commands sent over UDP into gz, which is not
lockstepped with PX4, so a command lands on a different IMU tick per run; tracking spreads of the same order with
the window anchored on the logged mode change (<30 % relative on non-floor metrics). (d) in force. Thresholds not
changed. Remedy candidates (stage 1, before G3): lockstep gz, or switch modes inside PX4 at a scheduled sim time.
Effort metric: raw derivative RMS is sample-rate dependent (A-11, closed s17), so G4 effort is defined at a fixed
bandwidth on a uniform grid.
