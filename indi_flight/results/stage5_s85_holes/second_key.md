# S85 hole reporter: second key

Verdict: AGREE WITH MINOR (no change needed for PASS on the s84 hf flight; four hardening notes).

## Recount (own pyulog script, raw timestamps after the first second, gap = dt > 1.5 x median)
| flight.ulg stage5_s84_accbreak/hf | median | samples | gaps | gap sizes | reporter hf.json |
|---|---|---|---|---|---|
| sim_ground_truth | 2.5 ms (400 Hz) | 44355 | 5 | 4 x 5.0 ms, 1 x 6.25 ms | sim count 5, max 6.25 ms |
| vehicle_angular_velocity | 2.5 ms | 44363 | 1 | 1 x 5.0 ms | controller count 1, max 5.0 ms |
| actuator_motors | 2.5 ms | 44363 | 1 | 5.0 ms | consistent |
No duplicate stamps and no non-monotonic stamps in this flight, so the dup rule is not exercised here. Missing by span/median - n is 1 and 1, gap sum 5 and 1; sim 5/44360 = 0.011 %, matching 0.0113 %. Logger dropouts 0. All three match exactly.

## Findings
1. hole_report.py:47-54 (dup cancel). Cancels a one-sample gap (dt <= 2 med) against any dt==0 within 8 samples. A real lost sample next to a duplicate is hidden. Not a false pass on the data checked: on stage5_s83_stick/indi_posctl, span/median - n = 2 for all three controller topics and the reporter reports 2, so the cancel is correct there. Hardening: also cross-check count-based missing = span/med - n_unique(+dups) and fail on disagreement; the cancel is otherwise only a heuristic. (Minor)
2. hole_report.py:92,105-108 (match tolerance). Controller gaps within +-max(med, 1.25 ms) of a sim gap are attributed to sim, and only the sim gap is held to the 10 ms limit. A 12 ms controller hole next to a 2.5 ms sim hole is classed sim and passes. Suggest checking max controller dt irrespective of attribution. (Minor)
3. hole_report.py:81-92 (sim-info). Decimated *_groundtruth are info-only, so a run whose only sim evidence is those topics reports sim holes undetected; with sim_ground_truth or sensor_gyro present (both full rate in hf and indi_posctl, 0 gaps) this is acceptable. In indi_posctl the groundtruth topics lose 7615 samples, so they would be useless as hole detectors; recommend the reporter fail or warn "sim: not assessable" if neither primary topic is present. (Minor)
4. Denominator, hole_report.py:64: missing/(missing+n) counts duplicate stamps in n (about 1.5 % of controller samples in indi_posctl): negligible effect (about 1e-5 relative). No issue.

Not found: the first-second skip, rate from median, and 10 ms rule match the spec.
