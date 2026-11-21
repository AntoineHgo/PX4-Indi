# G4 truth-signal check (S168) -- PROBE, not gate evidence

Purpose (G4 R20/R4): check that hook 10c741af4b publishes the true rotor speed on esc_status instance 1 under
SIM_GZ_ESC_FB=2 (the eRPM telemetry model INDI flies), logged at about controller rate, different from instance 0.

Commands (repo root):
- `timeout 1600 indi_project/docker/run.sh -n s168build -t 1500 -- make px4_sitl_default` (build.log)
- `timeout 900 indi_project/docker/run.sh -n s168fly -t 900 -- python3 indi_flight/bench/run_scenario.py --scenario hover
  --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/g5_freeze_s157/params.params
  --gps-dly 110 --gnss-delay 110 --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0 --out indi_flight/results/g4_truth_s168/hover_typ_s1`
  (freeze params, typical noise profile D-NOISE-PROF)

## Result
Flight ok (exit ok, HEAD 250f4490f6, SITL rebuilt, build rc 0). `check_truth.py` (pyulog, Docker; output above in session):
- esc_status instances [0, 1] both logged at 800 Hz (median dt 1.25 ms, max 6.2 ms); instance 1 starts later (56657 vs 61993 samples).
- Window 40-70 s after first sample: both mean ~9520-9526 rpm per motor; instance 0 has 56 distinct values on motor 0
  (100 eRPM rounding), instance 1 has 598 (1 rpm): instance 1 is not the telemetry model.
- motor 0 inst0 - inst1: mean 5.7 rpm, rms 7.9 rpm, max 51 rpm; cross-correlation lag 1 sample (instance 0 one telemetry
  frame behind), as the eRPM model specifies. The 5.7 rpm mean offset is within the rounding step (100 eRPM / pole pairs).
- `bench/g4_metrics.py` now selects the instance from SIM_GZ_ESC_FB (FB 2 -> instance 1, truth) or `--esc-instance`;
  selftest PASS. Window 58-72 s: truth R20 0.770 rad/s = 0.077 % hover, R4 2.60 rad/s = 0.262 %, C20 0.0014, clip 0
  (g4_metrics_inst1.json); proxy instance 0: R20 0.090 %, R4 0.268 % (g4_metrics_inst0.json). Probe only.
NOTE (later S168): the 58-72 s window runs past the hold end (62.0 s); hold-window values in ../g4_pretest_s168/README.md.
Verdict: hook works as specified on the log (G4 R20/R4 truth signal available). Key2 of the hook: key2_hook.md.
