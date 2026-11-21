# G3 set-up fixes (S175), bench tooling only

## (1) Cause of g4_typical_noise not_applied on 20/20
`bench/g3_run.py` hard-coded `not_applied["g4_typical_noise"] = "hook missing"` and never passed `--imu-noise-scale`
(only the drawn `--vib-acc/--vib-gyr`). `gate_g4.sh` "typ" passes `--vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0`
(D-NOISE-PROF), and run_scenario.py already supports all three (SIM_GZ_IMU_NSC / SIM_GZ_VIB_*). The hook existed; the driver did not use it.
Fix: g3_run.py now passes `--imu-noise-scale 4.0` and `--vib-acc = 10 + drawn`, `--vib-gyr = 0 + drawn`, and records
`applied["g4_typical_noise"]`. CHOICE, UNVERIFIED by owner: GATES says the typical profile is "added underneath" the drawn
vibration; there is one rotor line in gz_bridge, so the amplitudes are summed (same line, in phase, conservative).
Alternative: drawn x1..x5 replaces the 10 m/s^2 line (then acc = drawn only). Say if you want that.

## (2) Abort before flying
`g3_run.main()` builds every selected draw first; if any `not_applied` is non-empty it prints `ABORT run_NNN ...` and
`refusing to fly` to stderr and exits 3, before creating any file (also under --dry-run). Consequence: any draw with
`tel_frozen.on` (about 2 of 20 in seed 173, runs 03, 11) now aborts the whole invocation; run the batch with `--start/--stop`
excluding those indices, or build the hook.
Self-test: `bench/tests/test_g3_run.py::test_unsupported_factor_aborts_before_flying` (spec with tel_frozen on: `unapplied()`
reports it; real `g3_run.py` subprocess, with and without --dry-run, exits non-zero, message present, out dir empty), plus
`test_typical_profile_in_argv`. Run: `python3 bench/tests/test_g3_run.py` (all PASS; pytest is not installed on the host).
Break-check: with the abort branch disabled (`if bad:` -> `if False:`) the new test FAILS ("break caught"); restored, PASS.

## (3) Scoring in Docker
`bench/g3_score.sh RESULTS_DIR` (S174 score.sh, directory now an argument) and wrapper `bench/g3_score_docker.sh RESULTS_DIR`:
`bash indi_flight/bench/g3_score_docker.sh indi_flight/results/<dir>` (uses indi_project/docker/run.sh in place, image px4-indi-sim, scipy present).
Checked on a copy of pre-test run_000 (results/g3_setup_s175/score_check/): runs, writes g3_checks.json/txt, overall `pass` false = same as the S174 scratchpad result.
Detail differs from the S174 json (new keys max_ratio etc., fewer flagged windows) because g3_checks.py changed after S174 (bd6afcdcdd, Q14/Q15, D-G3-SPAN), not because of Docker. The ulg copy was deleted.

## (4) SITL pre-check, results/g3_setup_s175/run_000
NOT a hover: g3_run has no hover scenario, so I re-flew draw 0 of seed 173 (o1_lemniscate, position, ~100 s wall, 1:43) through g3_run.py
in Docker, same draw as pre-test run_000 (typical not applied), an exact A/B. Outcome ok, validity valid, not_applied = {}.
ulg initial params: SIM_GZ_IMU_NSC 1.0 -> 4.0, SIM_GZ_VIB_ACC 1.23 -> 11.23 (drawn 1.23 + 10), VIB_RPM 9540.
sensor_accel HF noise (std of first difference / sqrt2, t0+5..25 s): old x,y,z 0.539, 0.539, 0.378 m/s^2 -> new 4.92, 4.92, 3.46 (x9.1).
Gyro unchanged (0.027 -> 0.027 xy): NSC 4.0 is accel-heavy per D-NOISE-PROF and gyro line is 0. Not checked: G4 PSD line amplitude (bench/vib_line_check.py) on this run.

## tel_frozen hook, what it needs (not built)
- bench/run_scenario.py: a scenario-override kind (like `erpm_loss` in bench/scenario_overrides.py) `erpm_frozen`: motor, start offset, duration.
- gz_bridge side or bench-side injector that repeats the previous esc_status rpm bit-identical for the motor for FROZEN_S (1 s) in sim time
  (gz_bridge change is out of scope here; needs the esc_status publish path in src/modules/simulation/gz_bridge).
- g3_run.py: replace `not_applied["tel_frozen"]` by an `ov["erpm_frozen"]` entry + applied record; update the two tests that expect "hook missing".
