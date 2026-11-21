# G4 scores, freeze-7 (S177), 18 runs, both keys

Runs: `g4/{hover,cruise}_{quiet,typ,harsh}_s{1,2,3}` (rc 0). Same scripts and rules as freeze-6 rescore_s175.md / rescore_key2_s175.md
(Q14 A line RMS +-2 Hz >= 5e-4 and ratio > 20; Q15 A nav_state skip), no script or threshold edited. Commands (repo root, Docker, the old
scripts with the path `results/g4_gate_s169` replaced by `results/freeze7_s177/g4` through sed into python stdin):
```
indi_project/docker/run.sh -n g4f7 -t 900 -- sh -c "sh indi_flight/bench/gate_g4.sh score indi_flight/results/freeze7_s177/g4; sed 's#results/g4_gate_s169#results/freeze7_s177/g4#' indi_flight/results/g4_gate_s169/rescore_s175.py | python3 -"   # key 1
indi_project/docker/run.sh -n g4k2 -t 900 -- sh -c "sed 's#results/g4_gate_s169#results/freeze7_s177/g4#' indi_flight/results/g4_gate_s169/rescore_key2_s175.py | python3 -"   # key 2
indi_project/docker/run.sh -n chc7 -t 900 -- python3 indi_flight/results/g4_gate_s169/chatter_cruise_s176.py g4/cruise_*_s?   # raw: chatter_raw_s177.txt
```
Generated: `g4/g4_table.md`, `g4/rescore_s175_runs.md` (key 1), `g4/<run>/g3_checks_s175.json`. Key 2 table is stdout only (copied below).
The chatter script is cruise-only (KeyError 'traj' on hover, run with hover_harsh dirs appended): hover has no phase breakdown, key 2 peak frequency only.

## Per-flight table
R20/C20/R4/clip identical for both keys (same g4_metrics). Limits: R20 <= 1.0/1.5/3 %, C20 <= .004/.006/.012, R4 <= 3/4/6 %, clip 0/0/<=0.1 %;
cruise R20, C20 = hover limit x1.5. Item 2 column = the whole airborne item 2 as the script reports it (key 1: rate detector plus command chatter;
key 2: rate detector only, chatter separate). K1 rate = p/q/r sustained flags of key 1.

| run | R20 % | C20 | R4 % | clip | K1 chatter | K1 line RMS max (ratio>20) | K1 rate p/q/r | K1 item 2 | K2 chatter | K2 peak Hz (ratio, line RMS) | K2 item 2 rate (max rms dps p/q/r) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hover_quiet_s1 | 0.003 | 0.00003 | 0.009 | 0.0000 | no | 2.29e-04 | -/-/- | PASS | no | 39.0 (6893, 1.40e-04) | pass (0.4/0.4/0.0) |
| hover_quiet_s2 | 0.003 | 0.00003 | 0.009 | 0.0000 | no | 2.21e-04 | -/-/- | PASS | no | 22.2 (7508, 1.49e-04) | pass (0.3/0.4/0.0) |
| hover_quiet_s3 | 0.003 | 0.00003 | 0.010 | 0.0000 | no | 2.26e-04 | -/-/- | PASS | no | 39.0 (6965, 1.39e-04) | pass (0.4/0.4/0.1) |
| hover_typ_s1 | 0.016 | 0.00025 | 0.043 | 0.0000 | no | 2.69e-04 | -/-/- | PASS | no | 39.0 (693, 1.46e-04) | pass (0.6/0.9/0.0) |
| hover_typ_s2 | 0.016 | 0.00025 | 0.042 | 0.0000 | no | 2.76e-04 | -/-/- | PASS | no | 39.0 (573, 1.41e-04) | pass (0.3/0.4/0.0) |
| hover_typ_s3 | 0.016 | 0.00025 | 0.042 | 0.0000 | no | 2.59e-04 | -/-/- | PASS | no | 39.0 (732, 1.39e-04) | pass (0.5/0.4/0.0) |
| hover_harsh_s1 | 0.039 | 0.00061 | 0.100 | 0.0000 | CHATTER | 9.65e-04 | -/-/- | FAIL | CHATTER | 20.0 (1353, 9.74e-04) | pass (1.9/0.6/0.0) |
| hover_harsh_s2 | 0.039 | 0.00061 | 0.098 | 0.0000 | no | 9.17e-04 | -/-/- | PASS | no | 20.0 (706, 9.44e-04) | pass (0.5/0.3/0.0) |
| hover_harsh_s3 | 0.039 | 0.00061 | 0.097 | 0.0000 | no | 8.98e-04 | -/-/- | PASS | no | 20.0 (904, 9.12e-04) | pass (0.2/0.4/0.0) |
| cruise_quiet_s1 | 0.059 | 0.00163 | 0.299 | 0.0000 | CHATTER | 1.47e-03 | -/-/- | FAIL | CHATTER | 33.2 (12146, 1.50e-03) | pass (2.3/2.2/0.8) |
| cruise_quiet_s2 | 0.059 | 0.00162 | 0.303 | 0.0000 | CHATTER | 1.41e-03 | -/-/- | FAIL | CHATTER | 33.5 (543, 1.44e-03) | pass (2.2/2.1/0.7) |
| cruise_quiet_s3 | 0.060 | 0.00165 | 0.326 | 0.0000 | CHATTER | 1.46e-03 | -/-/- | FAIL | CHATTER | 33.2 (2677, 1.48e-03) | pass (2.2/2.6/0.7) |
| cruise_typ_s1 | 0.061 | 0.00169 | 0.370 | 0.0000 | CHATTER | 1.47e-03 | -/-/- | FAIL | CHATTER | 33.2 (3892, 1.48e-03) | pass (4.3/3.7/1.1) |
| cruise_typ_s2 | 0.060 | 0.00168 | 0.375 | 0.0000 | CHATTER | 1.51e-03 | -/-/- | FAIL | CHATTER | 33.5 (2404, 1.52e-03) | pass (4.1/3.7/1.1) |
| cruise_typ_s3 | 0.061 | 0.00168 | 0.360 | 0.0000 | CHATTER | 1.45e-03 | -/-/- | FAIL | CHATTER | 33.0 (439, 1.48e-03) | pass (4.4/4.2/1.1) |
| cruise_harsh_s1 | 0.065 | 0.00190 | 0.634 | 0.0000 | CHATTER | 1.41e-03 | -/-/- | FAIL | CHATTER | 33.2 (997, 1.46e-03) | FLAG p,q (11.7/11.4/3.0) |
| cruise_harsh_s2 | 0.064 | 0.00189 | 0.603 | 0.0000 | CHATTER | 1.47e-03 | S/S/- | FAIL | CHATTER | 33.2 (725, 1.45e-03) | FLAG p (12.9/11.3/3.0) |
| cruise_harsh_s3 | 0.065 | 0.00191 | 0.636 | 0.0000 | CHATTER | 1.42e-03 | S/S/- | FAIL | CHATTER | 33.2 (795, 1.45e-03) | FLAG p,q (11.9/11.6/3.1) |

## Row verdicts (both keys, same table values)
| row | result |
|---|---|
| R20 | 18/18 PASS (max 0.065 % cruise harsh vs limit 4.5 %) |
| C20 | 18/18 PASS (max 1.9e-3, cruise harsh limit 0.018) |
| R4 | 18/18 PASS (max 0.636 %) |
| clip fraction | 18/18 PASS (all 0) |
| item 1 LOC (harsh hover) | 3/3 PASS (18/18 in table) |
| item 3 steady state (harsh hover) | 3/3 PASS (cruise item 3 not meaningful, ignore) |
| item 2 rate detector, harsh hover (Q15 skip) | 3/3 PASS, both keys; hover 9/9 no sustained p/q/r |
| item 2 rate detector, cruise (informational, outside harsh-hover scope; freeze-6 key 1 -/-/-, key 2 pass) | NEW: harsh cruise key 1 sustained p,q in s2, s3; key 2 flags p (s2) or p,q (s1, s3), 11.3-12.9 dps vs 5 dps; quiet/typ pass both keys |
| command chatter, hover 9 | key 1 8/9 PASS, key 2 8/9 PASS; only hover_harsh_s1 CHATTER (4 motors, 20.0 Hz, RMS 9.7e-4) |
| command chatter, cruise 9 | key 1 0/9 PASS, key 2 0/9 PASS (CHATTER 9/9, all 4 motors) |

## Chatter lines (cruise, from chatter_raw_s177.txt, key1 +-2 Hz; per run order harsh s1-3, quiet s1-3, typ s1-3)
Floor = 5e-4 line RMS. nav_state: 4 loiter, 17 takeoff (7-14 s), 14 offboard (29-59 s), 18 land (70 s).
| line | where | peak/floor | present in |
|---|---|---|---|
| 33.2-33.5 Hz | traj-cruise (flagged 35-53 s, 25-26 of 28 windows) | 1.4-1.5e-3, 2.8-3.0x | 9/9 cruise, new vs freeze-6 (replaces the 89 Hz line) |
| 89 Hz | none | not seen in any flagged span or key 2 peak | 0/9 cruise: GONE (the one 88.8 Hz peak of freeze-6 key 2 has no counterpart) |
| 20-22.5 Hz | AUTO_LAND, 64-72 s (land-cmd windows) | 1.8-4.8e-3, 3.6-9.6x (max cruise_harsh_s2 4.8e-3) | 9/9 cruise, still present (freeze-6: 4-8.6x, same range) |
| 20-23 Hz | early takeoff/loiter 11-18 s | 5.6-9.9e-4 | only 3 cruise_harsh runs (s1-s3) |
| 54.8 / 22 Hz | 57-63 s hold to land transition | 6.0-7.2e-4 | harsh s1-s3 only |
Quiet/typ cruise have no 11-18 s line; their only spans are 33.x Hz (35-53 s) and 20.0-20.3 Hz land (65.5-72 s), line RMS 1.8-2.8e-3.
Hover: key 2 peak 20.0 Hz in harsh (RMS 9.1-9.7e-4, ratio 706-1353), sustained only in s1; quiet/typ peak at 39 Hz or 22 Hz with RMS 1.4e-4 (below floor).
Hover phase of the 20.0 Hz line (probably land entry as in freeze-6) NOT localised (the cruise script does not run on hover).

## Comparison to freeze-6
Metric rows 18/18 PASS and harsh-hover item 2 PASS unchanged; chatter hover 6/9 FAIL (key 1, width-fixed) -> 1/9 FAIL (8/9 PASS) in both keys; cruise chatter 9/9 FAIL
unchanged in count, 89 Hz line gone but replaced by a 33 Hz line (2.8-3x floor) in the lemniscate, and the 20-22 Hz AUTO_LAND line persists; harsh cruise now also shows sustained p/q rate flags.
