# G4 re-score S175 (Q14 A, Q15 A), key1 only

## Rules applied (bench/g3_checks.py)
- Q14 A: a 20-100 Hz line in actuator_motors is chatter only if peak > 20 x median AND line RMS (periodogram density integrated over peak +-2 bins,
  about +-2 Hz at the 4 s window's 0.25 Hz bin) >= `CMD_LINE_RMS` = 5e-4 (one DShot step). Ratio still reported (`max_ratio`, `rms_at_max_ratio`,
  `max_rms_ratio_flagged` per motor in the JSON). The existing rate-detector RMS test changed from `>` to `>=` (no practical effect).
- Q15 A: with `--skip-nav-change` (evaluate(nav_changes=...)) the p,q,r detector does not evaluate any 4 s window overlapping [t, t+3 s] after a
  vehicle_status.nav_state change (every change, first sample excluded). Skipped windows count as unflagged (they break a run) and are reported
  (`skipped_windows`). Off by default (G3 unchanged); the G4 re-score uses it. Chatter is NOT skipped (no owner rule for it).
- Windows for item 1/3: last 10 s of the hold (hover) or traj (cruise) event, as A-55. Item 2 spans the whole airborne span (D-G3-SPAN).
  Item 3 on cruise rows is not meaningful (hover reference), ignore.

## Per-run table (rescore_s175_runs.md, generated)
Columns: R20/C20/R4/clip from g4_table.md (unchanged by the rules). Chatter: max peak/median over motors and windows, line RMS in that window,
largest line RMS among windows with ratio > 20, verdict. skipped windows p/q/r of about 81.
| run | R20 % | C20 | R4 % | clip | chatter peak ratio (max) | line RMS at max ratio | line RMS max (ratio>20) | chatter | item 2 p/q/r | skipped windows | item 2 | item1 | item3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| cruise_harsh_s1 | 0.041 | 0.00150 | 0.765 | 0.0000 | 3156 | 2.42e-04 | 3.11e-03 | CHATTER | -/-/- | 19/19/19 | FAIL | PASS | FAIL |
| cruise_harsh_s2 | 0.042 | 0.00150 | 0.764 | 0.0000 | 2770 | 2.51e-04 | 1.88e-03 | CHATTER | -/-/- | 20/20/20 | FAIL | PASS | FAIL |
| cruise_harsh_s3 | 0.041 | 0.00148 | 0.760 | 0.0000 | 2773 | 2.47e-04 | 2.60e-03 | CHATTER | -/-/- | 20/20/20 | FAIL | PASS | FAIL |
| cruise_quiet_s1 | 0.029 | 0.00104 | 0.324 | 0.0000 | 7269 | 3.79e-04 | 8.23e-04 | CHATTER | -/-/- | 19/19/19 | FAIL | PASS | FAIL |
| cruise_quiet_s2 | 0.029 | 0.00104 | 0.328 | 0.0000 | 9604 | 1.35e-04 | 6.81e-04 | CHATTER | -/-/- | 19/19/19 | FAIL | PASS | FAIL |
| cruise_quiet_s3 | 0.030 | 0.00106 | 0.346 | 0.0000 | 5976 | 6.51e-04 | 6.66e-04 | CHATTER | -/-/- | 19/19/19 | FAIL | PASS | FAIL |
| cruise_typ_s1 | 0.031 | 0.00111 | 0.411 | 0.0000 | 1572 | 1.68e-03 | 1.97e-03 | CHATTER | -/-/- | 19/19/19 | FAIL | PASS | FAIL |
| cruise_typ_s2 | 0.031 | 0.00111 | 0.410 | 0.0000 | 946 | 6.29e-04 | 2.97e-03 | CHATTER | -/-/- | 19/19/19 | FAIL | PASS | PASS |
| cruise_typ_s3 | 0.031 | 0.00113 | 0.422 | 0.0000 | 1611 | 1.69e-03 | 1.78e-03 | CHATTER | -/-/- | 19/19/19 | FAIL | PASS | PASS |
| hover_harsh_s1 | 0.032 | 0.00051 | 0.081 | 0.0000 | 3103 | 2.51e-04 | 1.81e-03 | no | -/-/- | 20/20/20 | PASS | PASS | PASS |
| hover_harsh_s2 | 0.034 | 0.00053 | 0.084 | 0.0000 | 3415 | 2.48e-04 | 3.87e-03 | CHATTER | -/-/- | 19/19/19 | FAIL | PASS | PASS |
| hover_harsh_s3 | 0.034 | 0.00053 | 0.084 | 0.0000 | 3214 | 2.53e-04 | 9.13e-04 | no | -/-/- | 19/19/19 | PASS | PASS | PASS |
| hover_quiet_s1 | 0.003 | 0.00003 | 0.009 | 0.0000 | 7586 | 1.41e-04 | 7.27e-04 | no | -/-/- | 19/19/19 | PASS | PASS | PASS |
| hover_quiet_s2 | 0.003 | 0.00003 | 0.009 | 0.0000 | 7641 | 1.41e-04 | 8.14e-04 | no | -/-/- | 19/19/19 | PASS | PASS | PASS |
| hover_quiet_s3 | 0.003 | 0.00003 | 0.009 | 0.0000 | 8129 | 1.42e-04 | 1.88e-04 | no | -/-/- | 19/19/19 | PASS | PASS | PASS |
| hover_typ_s1 | 0.015 | 0.00023 | 0.042 | 0.0000 | 637 | 1.38e-04 | 2.40e-03 | CHATTER | -/-/- | 19/19/19 | FAIL | PASS | PASS |
| hover_typ_s2 | 0.013 | 0.00020 | 0.038 | 0.0000 | 2342 | 1.61e-03 | 1.68e-03 | CHATTER | -/-/- | 19/19/19 | FAIL | PASS | PASS |
| hover_typ_s3 | 0.014 | 0.00022 | 0.038 | 0.0000 | 1503 | 1.50e-03 | 1.79e-03 | CHATTER | -/-/- | 19/19/19 | FAIL | PASS | PASS |

## G4 row verdicts (limits GATES 4; cruise R20/C20 = hover x 1.5; chatter and item 2 are the "Additional" row)
| row | result |
|---|---|
| R20 | 18/18 PASS (hover 9/9, cruise 9/9) |
| C20 | 18/18 PASS |
| R4 | 18/18 PASS |
| clip fraction | 18/18 PASS (all 0) |
| item 1 LOC (harsh hover) | 3/3 PASS (all 18 PASS in the table) |
| item 3 steady state (harsh hover) | 3/3 PASS (hover 9/9) |
| item 2 on body rates (Q15 rule, harsh hover) | 3/3 PASS; hover 9/9 no sustained p/q/r. Without the skip, hover_harsh_s2 flags q 2.0 Hz, window 82 (land entry), as before; the skip removes it (19 of 81 windows skipped per run, 3 nav changes). |
| command chatter, Q14 rule, harsh hover | 2/3 PASS (s1, s3); **s2 FAIL** |
| command chatter, all 9 hover runs | 5/9 PASS: quiet 3/3, harsh s1 s3; typ 0/3 FAIL, harsh s2 FAIL |
| command chatter, cruise (informational) | 0/9 PASS (22 Hz and 88.8 Hz lines, line RMS 0.7e-3 to 3e-3) |

Cause of the chatter FAILs (hover): the flagged windows start at index 83-84 of the airborne span (about 94-95 s), i.e. the AUTO_LAND entry
(t_land about 96 s): a 20.5-23 Hz command line of RMS 1.6e-3 to 3.9e-3 (3 to 8 DShot steps) in 3-4 consecutive windows on all four motors
(hover_typ_s1 on 2 motors; harsh_s2 largest, 3.9e-3). It is a land-entry feature, not hover: in the harsh hover s1/s3 and quiet runs the ratio
is still large (3000-8000) but line RMS stays below 5e-4 or flags no 3 consecutive windows. Not covered by Q15 (rates only). Needs an owner
decision (extend the nav_state skip to the command chatter, or accept as the land-entry transient); NOT applied here.
Overall G4 (hover scope, as the criteria text reads): FAIL on the chatter clause only (typ 3 runs, harsh s2), everything else PASS.
If the owner extends the Q15 skip to chatter, re-score is one flag away (not run).

## PID reference logs (item 2 only, rescore_pid_s175.md)
| PID run | item 2 p/q/r sustained, no skip | item 2 p/q/r sustained, Q15 skip | skipped windows p/q/r | chatter (Q14 rule) |
|---|---|---|---|---|
| a54_s169/pid_hover_harsh_s1 | -/-/- | -/-/- | 20/20/20 | no |
| a56_pid_s173/pid_hover_harsh_s2 | -/-/- | -/-/- | 20/20/20 | no |
| a56_pid_s173/pid_hover_harsh_s3 | -/-/- | -/-/- | 19/19/19 | no |

PID logs found: a54_s169/pid_hover_harsh_s1, a56_pid_s173/pid_hover_harsh_s2, s3 (none in a56_rate_s174 itself). No sustained p/q/r with or
without the skip, chatter none. Land-entry transient in both stacks (from a56_rate_s174/README.md): INDI q std peak 9-25 deg/s over 1-2 s,
PID 16-30.5 deg/s over 2-2.5 s; with the skip it is excluded from the detector for both, INDI harsh s2 is the only run the detector flagged without it.

## Test and break-check log
`bench/tests/test_g3_checks.py` extended (make() got line_amp, cmd_noise, osc_until, nav_changes) with chat_lowrms (ratio > 20, RMS 4e-4 -> not chatter),
chat_hirms (RMS 1e-3 -> chatter), burst_in_nav (3 s burst 60-63 s, nav change 60 s -> not flagged, skipped windows > 0), burst_later (burst 70-73 s -> flagged).
All 13 cases pass (`selftest PASS`). Break-checks (each once, rule reverted, test must go red):
- chat_hirms: CMD_LINE_RMS patched to 1e9 -> case fails (break caught), via `--break-check`.
- burst_in_nav: skip disabled (nav_changes=None) -> burst flagged, case fails (caught), via `--break-check`. (First attempt, NAV_SKIP_S=0, was NOT caught
  because windows starting inside the burst still flag; replaced.) `--break-check` ends PASS.
- chat_lowrms: CMD_LINE_RMS = 0 -> item 2 FAIL (caught); burst_later: NAV_SKIP_S = 1e6 (skip everything) -> item 2 passes, burst missed (caught).
  Both by `breakcheck_extra_s175.py` (ad hoc, not in the test file's --break-check).
Rules were restored after each (patches are in-process only; source never edited for the checks).

## Commands (repo root, Docker; scipy/pyulog are not on the host)
```
indi_project/docker/run.sh -n g3t -t 600 -- sh -c "python3 indi_flight/bench/tests/test_g3_checks.py; python3 indi_flight/bench/tests/test_g3_checks.py --break-check"
indi_project/docker/run.sh -n bc  -t 300 -- python3 indi_flight/results/g4_gate_s169/breakcheck_extra_s175.py
indi_project/docker/run.sh -n g4rs -t 900 -- sh -c "sh indi_flight/bench/gate_g4.sh score indi_flight/results/g4_gate_s169 && python3 indi_flight/results/g4_gate_s169/rescore_s175.py"
indi_project/docker/run.sh -n g4rp -t 900 -- python3 indi_flight/results/g4_gate_s169/rescore_pid_s175.py
indi_project/docker/run.sh -n ns -t 300 -- bash indi_flight/results/g4_gate_s169/noskip_s175.sh   # harsh/typ/quiet hover without the skip
```
Not changed: gate_g4.sh, g4_metrics.py (score mode only produces R20/C20/R4/clip; item 2 is rescore_s175.py calling g3_checks.py --skip-nav-change).
Side effect: `gate_g4.sh score` also rewrote g4_table.md (identical values) and, once by mistake, a56_rate_s174/bld03/g4_table.md.
UNVERIFIED: the 22 Hz land-entry line source; cruise item 2/chatter scoping (spec text is ambiguous); window RMS definition is the existing one (+-2 bins).
