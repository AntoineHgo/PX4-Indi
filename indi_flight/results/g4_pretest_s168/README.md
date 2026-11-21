# G4 pre-test (S168) -- PRE-TEST, 1 seed, not gate evidence

Purpose (G4, lesson 23): show the configuration flies at each profile, the scenarios do what they claim, the truth
signal is logged, and the metric runs, before the 27-run batch. Firmware/SITL at 250f4490f6 (freeze firmware
23acbdef67 + gz_bridge true-rpm hook), freeze params `g5_freeze_s157/params.params`, matched GNSS 110 ms, SIM_GZ_ESC_FB=2.
Profiles (D-NOISE-PROF): quiet `--vib-acc 0.5 --imu-noise-scale 1.0`, typical `--vib-acc 10 --imu-noise-scale 4.0`,
harsh `--vib-acc 27 --imu-noise-scale 4.0`, all `--vib-gyr 0`. Fly: `chain.sh`; score: `score.sh` (Docker, repo root),
window = hold event + 5 s .. end (hover), trajectory event + 3 s ramp .. end (cruise), times relative to the ulog start.

| run | scenario | window (s) | R20 % hover | R4 % | C20 | C4 | clip |
|---|---|---|---|---|---|---|---|
| hoverL_quiet_s1 | hover_long (60 s) | 37.1-92.1 | 0.003 | 0.009 | 0.00003 | 0.00005 | 0 |
| hover_typ_s1 (g4_truth_s168, 30 s hold) | hover | 37.0-62.0 | 0.014 | 0.038 | 0.00023 | 0.00042 | 0 |
| hoverL_harsh_s1 | hover_long (60 s) | 37.0-92.0 | 0.034 | 0.085 | 0.00053 | 0.00100 | 0 |
| lemn_typ_s1 | traj_lemniscate (5 m/s) | 37.9-52.1 | 0.030 | 0.371 | 0.00108 | 0.00276 | 0 |

All 3 flights exit ok; esc_status instance 1 = truth (rotor_speed_is_truth true). Ordering quiet < typical < harsh is
monotone. Every value is >= 30x below the PROPOSED G4 limits (R20 1.0/1.5/3 %, C20 0.004/0.006/0.012, clip 0).
Window defect found: the S166 pre-look window 58-72 s (and the first S168 score in ../g4_truth_s168) runs past the
end of the hold (hold ends at 62.0 s on the log time base), so those numbers (R20 0.077-0.093 %) include the post-hold
segment; the hold-window value is the one above. Gate scoring must take windows from run.json events (score.sh does).
Pre-test verdict: configuration, scenarios, signals and metric OK. Acro row not flown (stick quantisation model
deferred, RC168). Key2 of the metric: key2_metrics.md.
Key2 (S168, sonnet, `bench/g4_metrics_key2.py`, written blind, self-test PASS): hover_typ_s1 and quiet agree within 1 %;
harsh R20 1.1 %, R4 0.4 %, C4 2.2 %, C20 7 % (key1 0.000532, key2 0.000495): open as A-52 (bound: 23x below limit).
lemn windows differ (key2 took the whole trajectory event incl. ramp), not compared.
