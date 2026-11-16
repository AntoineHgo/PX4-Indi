# S40 M3a injection pre-test (margin campaign gate)

Raw logs are untracked. Nothing committed.

Setup: hover, controller indi_m3a, model quad5in, seed 1, speed 4, timeout 420. Injection: axis 0 (roll), TP 10 s, NP 2, FMIN 1, FMAX 60 Hz, 18 components, equal amplitude AMP per component, controller 800 Hz.

- Build: `indi_project/docker/run.sh -n s40build -t 1500 'make px4_sitl_default'` rc 0 (incremental).
- Params: `inj_model.params` (S39 `inj.params`, AMP 0.005, DLY 5); `inj_measured.params` (same plus `CA_R_W_MAX 2700`).
- Rotor speed for CA_R_W_MAX: 2700 rad/s = `<maxRotVelocity>2700` on all 4 motor plugins in `indi_flight/sim/models/quad5in/model.sdf` (grep count 4). The runner maps CA_R_W_MAX to MC_INDI_W_MAX (`indi_flight/bench/run_scenario.py:652-653`).
- Checker: `checks.py` in this folder (run in the container); output `checks_all.txt`. `check_rates.py` output is in the same file.
- Stdout logs: `model_stdout.log` (rc_a=0), `measured_stdout.log` (rc_b=1).

## (a) model-only: `model/`

| # | Check | Result |
|---|---|---|
| 1 | Completed | runner rc 0, exit_status ok. Window 37.006 to 57.005 s: max abs roll 3.91 deg, max abs pitch 3.20 deg (whole run 3.91 / 3.46 deg). |
| 2 | indi_rate_status | 66091 samples, median 800.00 Hz, mean 799.52 Hz over 82.66 s, 28 gaps > 1.5 ms. actuator_torque_measured: absent (expected, measured path off). |
| 3 | fault / landed in window | fault 0 of 15984 samples in window (0 whole run). landed (sample-held) 0 of 15984 in window. Whole run landed 12612 of 66091 samples: the pre-takeoff ground phase, so "landed == 0 everywhere" is not true for the whole run, only for the window. |
| 4 | u = c + d | max abs error 7.45e-9 (roll, float32 rounding). Other axes 0. |
| 5 | generator | K = 18 components, f 1.00 to 50.10 Hz. My formula vs `margins_est.multisine`: 0.0. With t0 = timestamp_sample of the first nonzero sample (37.0063 s): max abs diff 2.95e-9 over 15984 samples in [0, 20) s; 15980 with abs(d) > 1e-6. With t0 - 1.25 ms: max diff 7.19e-3. So t0 matches. Max abs(d) outside the window: 0. |
| 6 | timing | armed 30.014 s; first armed & not-landed 32.006 s; t0 37.006 s. t0 - not-landed = 5.000 s (DLY 5). t0 - armed = 6.992 s. |

Window content: 15984 logged samples over 19.9987 s, so 16 controller cycles (1.25 ms each) were skipped inside the window (16000 nominal). Time base: timestamp_sample.

Altitude (vehicle_local_position, -z): 0.96 m at t0 (37 s), 2.06 m at 38 s, 4.17 m at 40 s, 4.71 m at 42 s, 4.94 m at 45 s, 5.00 m at 50 s, 5.01 m at 57 s. Height std 0.02 m over 45 to 57 s, so hover is settled from about 45 to 50 s. The first 8 to 10 s of the injection window are climb-out, not hover.

Verdict (a): NOT READY. Mechanics checks 2 to 6 pass, but the excitation starts during the climb (0.96 m at t0). Fix: raise DLY so t0 falls after hover is settled (about 47 s or later), e.g. DLY 15 (t0 about 47 s, window to 67 s), then re-fly and re-check. The DLY value is a suggestion, not verified by a flight.

## (b) measured rotor speed: `measured/`

Not flown. rc_b = 1, run.json exit_status "failed", error "no ulog". Stdout: `model variants are x500-only until the stage-1b port of model_variant.py`.

Cause: `--sim v2` sets `variant["rpm"] = True` (`run_scenario.py` around line 657). That makes the runner call `apply_model_variant` (line 680), which raises SystemExit for any model other than x500 (line 181). So `--sim v2` cannot run with quad5in as the runner stands. I did not work around it (x500 would change the airframe). Options for the user: port `model_variant.py` (stage 1b), or let `--sim v2` skip the variant path when no variant values are set.

Checks 1 to 6 for (b): UNVERIFIED (no ulog). actuator_torque_measured presence and rate: UNVERIFIED.

Verdict (b): NOT READY (not flown, runner blocker).

## Self-test of the checker (not a flight result)

The S39 log (`indi_flight/results/stage2_s39/pretest_m3a/hover`, AMP 0.02) has no timestamp_sample, so the checker fell back to `timestamp`. Its generator comparison gave max diff 2.9e-2 (t0) and 2.6e-2 (t0 - 1.25 ms). I attribute this to the time base (the publish timestamp is not the gyro sample time, and S39 had skipped cycles), not to the generator. This is inferred, not checked further. The S40 run with timestamp_sample matches to 3e-9, which supports the generator.

## Summary

1. (a) completed (rc 0), window max abs roll 3.91 deg, pitch 3.20 deg. (b) not flown: runner rejects `--sim v2` for quad5in.
2. (a) indi_rate_status 800.00 Hz median, 66091 samples, no actuator_torque_measured (expected). (b) UNVERIFIED.
3. (a) fault 0 and landed 0 in the window (whole run landed 12612 samples, pre-takeoff ground). (b) UNVERIFIED.
4. (a) max abs u - (c + d) = 7.45e-9. (b) UNVERIFIED.
5. (a) generator matches with t0 = first nonzero timestamp_sample (max diff 2.95e-9, 15980 samples above 1e-6); t0 - 1.25 ms does not match (7.19e-3). (b) UNVERIFIED.
6. (a) t0 is 5.000 s after first armed & not-landed (DLY 5 honoured); injection starts at 0.96 m, during climb.

Verdicts: (a) NOT READY (start during climb; raise DLY to about 15). (b) NOT READY (runner blocker: quad5in with `--sim v2`).

## Orchestrator follow-up (S40)
- (b) unblocked: `run_scenario.py` adds the `rpm` model variant only for x500 (quad5in/model.sdf already carries a
  per-step JointStatePublisher). New scenario `hover_long` (60 s hold): with DLY 20, NP 3, TP 10 the window is
  52-82 s, at 5.0 m, after the climb.
- measured_long (`inj_measured_long.params`, `--sim v2`): checks all pass (`checks_measured_long.txt`):
  measured_torque_in_use on all 23990 window samples, actuator_torque_measured 800 Hz, fault 0, landed 0,
  u = c + d 3.7e-9, generator 2.95e-9 at t0, height 4.99-5.01 m. READY.
- model_long (`inj_model_long.params`): try1 aborted by the runner (climb not finished by 46 s, `model_long_try1/`),
  re-fly passed every check (`checks_model_long.txt`). READY, with the climb margin noted in A-21.
- Metric runs on the output: `bench/m3a_csv.py` (ulog -> t,d,x,y with x = u, y = c) then
  `bench/m3a_margins_pretest.py` (margins_est.frf_periodic with the 18 known bins; the CLI's detect_bins found 922
  bins because the 10-16 skipped sim steps leak d's spectrum above its 1e-3 threshold). Neither script is second-keyed yet.
- Preliminary roll margins, 800 Hz, one run each: measured PM 61.4 deg / GM 12.2 dB / DM 35 ms
  (`margins_measured_long.txt`); model-only PM 25.3 deg / GM 4.3 dB / DM 16 ms (`margins_model_long.txt`), far below
  the linear model: A-21.
- Linearity (A-21 closing test 1, amplitude half): model-only AMP 0.01, seed 1 (`margins_model_long_a010.txt`,
  checks pass, max roll 7.2 deg): PM 26.3 deg at 4.56 Hz, GM 5.0 dB, DM 16 ms, vs AMP 0.005: 25.3 deg at 4.47 Hz,
  4.3 dB. Bins 4.0 and 5.0 Hz agree within 0.3 dB and 3 deg (G2 linearity rule: 1 dB / 5 deg). The gap to the
  linear model is not an amplitude effect. Seed repeat still to fly.
