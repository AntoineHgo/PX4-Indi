# A-23 test: 17 Hz pitch limit cycle, SITL hover (S44)

Result: both flights FAIL the A-23 pass criteria (see table). The INDI G1-derived flight shows a
different and much larger limit cycle (8.0 Hz dominant, motors at zero for about 46 % of samples).
Raw logs and checker output are in this folder; no firmware, bench script or indi_project file was changed.

## Setup
- Scenario `hover_long` (60 s hold, analysis window 52-82 s), model quad5in, seed 1, speed 4, `--sim v2`,
  runner `indi_flight/bench/run_scenario.py`, run in Docker via `indi_project/docker/run.sh -n NAME -t 900`.
- Command record reused: `indi_flight/results/stage2_s40/pretest_inj/measured_long/run.json`
  (scenario hover_long, sim v2, params file inj_measured_long.params).
- Checker: `indi_flight/bench/limit_cycle_check_s44.py LOG OUT_MD [LABEL]` (run in the Docker container).
- Stacks: `docker ps` was empty before the first flight and after each run (no stray containers).

## Flight 1: pid_hover (PASS/FAIL below)
- Params `a23_pid.params`: `MC_RATE_CTL_TYPE 0` (stock PID; no MC_INDI_* params). Runner label `--controller pid_default`.
  The runner only sets MC_INDI_EN when MC_RATE_CTL_TYPE is 1, so this flight runs PID.
- Command: `run_scenario.py --scenario hover_long --controller pid_default --seed 1 --speed 4 --model quad5in --sim v2 --params a23_pid.params --out pid_hover`
- exit_status ok, completed. Climb done 39.6 s, hover_thrust_estimate 0.13667. Commit 80bcd82dea, not dirty.
- Output: `pid_hover/limit_cycle.md`, `pid_hover/flight.ulg`, `pid_hover_stdout.log`.

## Flight 2: indi_g1derived
- Params `a23_indi_g1derived.params` = copy of `indi_flight/results/stage2_s40/pretest_inj/inj_measured_long.params` with:
  - `MC_INDI_INJ_AMP 0` (was 0.005; injection off). Other injection lines unchanged (AX 1, TP 10, NP 3, DLY 20).
  - `CA_R_W_MAX 2700` kept (from the copied file; it maps to MC_INDI_W_MAX, as in measured_long).
  - `MC_INDI_G1_R 1756` (as specified).
  - `MC_INDI_G1_P 1599.49`, from 1756 x (|px| / |py|) x (Ixx / Iyy):
    - |px| = |py| = 0.0795 m: `ROMFS/px4fmu_common/init.d-posix/airframes/4040_gz_quad5in` CA_ROTOR0_PX/PY (all four rotors are +-0.0795).
    - Ixx = 1.022e-3, Iyy = 1.122e-3 kg m^2: base_link `<inertial>` in `indi_flight/sim/models/quad5in_base/model.sdf`,
      which quad5in/model.sdf includes (`model://quad5in_base`). Rotor inertias are not included.
    - 1756 x 1 x 0.910873 = 1599.49.
  - `MC_INDI_G1_Y` not set (unchanged).
- Command: `run_scenario.py --scenario hover_long --controller indi_m3a --seed 1 --speed 4 --model quad5in --sim v2 --params a23_indi_g1derived.params --out indi_g1derived`
- exit_status ok, completed, no error. Output: `indi_g1derived/limit_cycle.md`, `indi_g1derived/flight.ulg`.

## Checker numbers (window 52-82 s since boot, 800 Hz logged)

| Metric | pid_hover | indi_g1derived |
|---|---|---|
| Completed | yes | yes |
| Motors < 0.005 fraction (control[0..3]) | 0, 0, 0, 0 | 0.460, 0.464, 0.464, 0.464 |
| Motor mean (control[0..3]) | 0.1367 | 0.2493 |
| Pitch dominant frequency | 0.586 Hz | 8.008 Hz |
| Pitch PSD peak / median (band 0.5 Hz to Nyquist 400 Hz) | 1.761e7 | 4.251e6 |
| Pitch sinusoid amplitude | 0.0041 rad/s | 0.0233 rad/s |
| Body-rate RMS x / y / z (mean removed) | 0.00389 / 0.00460 / 0.00094 rad/s | 0.04528 / 0.03683 / 0.4231 rad/s |
| torque_setpoint_achieved fraction (samples) | 1.0 (5991) | 0.0733 (5988) |
| Mean abs unallocated torque x / y / z | 4.3e-9 / 4.2e-9 / 4.2e-9 | 1.6e-8 / 1.7e-8 / 0.612 |
| A-23 check: PSD peak/median < 100 | FAIL (1.76e7) | FAIL (4.25e6) |
| A-23 check: motors < 0.005 on < 1 % of samples | PASS (0 %) | FAIL (46 %) |
| **Verdict** | **FAIL** (PSD criterion) | **FAIL** (PSD and motors) |

## Notes and UNVERIFIED items
- The 17 Hz peak of A-23 was not seen. The INDI G1-derived flight has its dominant pitch frequency at 8.0 Hz; the
  power at 17 Hz was not checked (the checker does not report it).
- The PSD peak/median criterion is ill-conditioned here: the PID flight has a near-noise-free spectrum (pitch RMS 0.005 rad/s),
  so its median is tiny and the ratio is 1.8e7 even with no limit cycle. The PSD criterion fails for PID too, so it does not
  separate the two flights. UNVERIFIED whether a different threshold would be meaningful.
- The G1 values follow the spec formula. Ixx and Iyy are the base_link values only (rotor inertias excluded), and the
  result has not been checked against a flight with other G1 values.
- The INDI flight holds about 2x the PID motor mean (0.249 vs 0.137), with motors at zero about half the time; this was
  not investigated further.
- Pitch RMS in the window is 0.037 rad/s on INDI vs 0.0046 on PID. The largest pitch-rate bin of the INDI flight is at 35 s (climb), outside the window.
- Only one seed (1) was flown per configuration. No retries were needed (no crash or abort).
