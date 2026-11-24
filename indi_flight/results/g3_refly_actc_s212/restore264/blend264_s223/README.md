# Blend probes S223 on the full G3 draw 264 (run index 24, C212 samples), speed 1

Recipe as `../blend_s223/README.md`, with the full-draw inputs of `../../speed1_s213/README.md`:
`G3_PARAMS=<q*.params> g3_chain.sh start <dir> 24 24 --samples indi_flight/results/g3_refly_actc_s212/samples --speed 1 --allow-binary 903eae63...`
(start output in `q*_chain_start.txt`). `q1.params`, `q2.params` = `g5_freeze_s157/params.params` (the S213 pin) with only the `MC_INDI_ACT_BLD` line edited (diff verified, one line each).
One flight each, flown sequentially, no retries, no infra aborts. Raw .ulg untracked. Analysis: `analyze.sh` (docker; tilt via `../scripts/tilt.py`, split via `indi_flight/bench/g3_item2_split.py`), output `analyze_out.txt`, `q*/split.json`.

Checks vs S213 speed-1 flight (`speed1_s213/indi_024`): `g3_draw.json` equal except `build` and `command`; the 39-element `command` differs only in the 3 path arguments (run dir, g3_params.txt, g3_scenario_overrides.json). Same samples, speed 1, same ACT_TC draw (`actc` equal).
CAVEAT: gate binary differs. S213 flew d220e19315c2; these flights use the current build 903eae63ceb1 (as in the S223 joint probes). Not rebuilt. So the comparison to the S213 column is draw- and params-equal but not binary-equal.

| | S213 original (ACT_BLD 1.0) | Q1 ACT_BLD 0.10 | Q2 ACT_BLD 0.05 |
|---|---|---|---|
| param in log | 1.0 | 0.10 | 0.05 |
| fault t [s] (EC_MAX change) | 59.02 | 58.70 | 58.72 |
| max tilt after fault [deg] | 106.0 (abort at 61.05 s) | 48.5 (at 71.92 s) | 47.9 (at 71.86 s) |
| LOC (>60 deg for 0.5 s) | yes | no | no |
| key1 item 1 / 2 / 3 | INVALID | PASS / FAIL / FAIL | PASS / FAIL / FAIL |
| key2 item 1 / 2 / 3 | INVALID | PASS / FAIL / FAIL | PASS / FAIL / FAIL |
| item 3 horiz RMS (limit 0.30), key1 = key2 | - | 0.371 | 0.362 |
| item 1 tilt max (scorer, deg) | - | 48.4 | 47.9 |

## Item 2 split (cut at fault, ulog-start base: Q1 44.83 s, Q2 44.84 s; see ../item2_split_s223/README.md)
| | whole run | pre-fault [0,f) | post-fault [f,end] |
|---|---|---|---|
| Q1 key1 | FAIL p 2.0 Hz from 43.3 s, q 2.0 Hz from 42.3 s and 54.3 s (rms max 22/57) | pass (max rms 2.6/3.2/0.1) | FAIL p from 53.8, q from 49.8 and 53.8 (rms 11/23) |
| Q1 key2 | FAIL p from 42.7, q from 41.7 | pass | FAIL p from 53.8, q from 49.8 (rms 11.5/22.6) |
| Q2 key1 | FAIL p from 43.3 and 50.3, q from 42.3 and 48.3, r from 44.3 (rms 20/49) | pass (max 2.6/3.1/0.1) | FAIL p from 50.8, q from 47.8 and 54.8 (rms 11/28) |
| Q2 key2 | FAIL p from 42.7, q from 41.7, r from 43.7 | pass | FAIL p from 50.8, q from 47.8 (rms 11.4/28.1) |

Reading: for both keys and both flights item 2 does not fail pre-fault. The whole-run lines start 1-3 s before the cut, i.e. in windows that straddle the fault (4 s windows). But, unlike the S222 joint runs, the cropped post-fault segment also contains sustained 2.0 Hz p and q lines (3+ windows, starting 3-5 s after the fault, 11-28 dps), so the item 2 failure is post-fault (fault-excited oscillation that persists), not only a straddling-window artefact. Q2 (0.05) has a stronger post-fault q line (28 dps) than Q1 (23 dps); n=1 each.

## Conclusions
- ACT_BLD 0.10 and 0.05 both remove the LOC on the full draw 264 (max tilt 48 deg vs 106 deg at abort), same as on the reduced joint case. Gate G3 is still not passed on this draw: item 2 fails (post-fault 2 Hz p/q line) and item 3 fails (0.36-0.37 vs 0.30) on both keys.
- Unverified: single flights, flight-to-flight spread unknown; binary differs from S213 (see above); PID reference for item 3 on this draw not re-measured here.
