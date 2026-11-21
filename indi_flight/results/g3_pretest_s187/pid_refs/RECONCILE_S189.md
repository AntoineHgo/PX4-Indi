# PID reference runs 03 and 16: key 1 vs key 2 reconciliation (S189)

Scope: existing scorers and outputs only. Re-run of key 1 (g3_checks.py via docker, same args as g3_score.sh) and key 2 (g3_checks_key2.py) on pid_refs/run_003 and run_016. Outputs in scratchpad `rec/`. No flight, no firmware change, nothing committed.

## Run 03 (position, wind, no sag; hold 62.271-65.271 s)

| item | key 1 (as scored) | key 2 | key 1 with --skip-nav-change |
|---|---|---|---|
| 1 LOC | pass (excursion 1.573 m, tilt 38.7 deg) | pass (same) | pass |
| 2 p / q / r | p no, **q sustained (2.5 Hz, 3 windows, rms 6.45 to 12.6 dps)**, r no | all no (q max rms in flagged windows 1.75 dps) | all no (q max rms 1.71) |
| 3 steady | pass (h_rms 0.129 m, alt -0.080 m) | pass (same) | pass |
| overall | **FAIL** (item 2 q) | **PASS** | PASS |

Cause: the q line is not in the hold. Key 1 has no nav-change skip (g3_score.sh does not pass --skip-nav-change; 0 windows skipped). Its three flagged windows sit at about 67-73 s on the ulog clock (grid starts at airborne start 21.16 s; mapping inferred, not separately checked), which is the landing/RTL entry (t_land 69.80 s). Key 2 applies the Q15 A skip (3 s after each nav_state change): 21 q windows skipped, covering 66.4-72.4 s. With the same skip, key 1 gives q not sustained, item 2 PASS, overall PASS. The residual q/p/r amplitude values agree within about 3 percent (key 2 1.75 vs key 1 1.71 dps); this is not verdict-relevant.

Verdict: PASS is the right reading. The q line is the landing-entry transient (same mechanism as A-56 in ANOMALIES.md), outside the hold. Key 1's FAIL comes from a missing skip in the scorer, not from the flight. UNVERIFIED: GATES.md line 555 words the Q15 A skip as "G4 item 2", and line 607 says both keys apply it to the command-chatter check; I did not confirm that G3 item 2 is meant to carry the same skip. If it is not, the owner must decide whether a landing transient counts in G3 item 2.

Consequence for the owner rule: the PID reference of INDI run 03 does not reproduce item 2 in the hold; this is not evidence of a test defect for run 03.

## Run 16 (attitude, no wind; hold 62.885-65.885 s)

| item | key 1 | key 2 |
|---|---|---|
| 1 LOC | pass (drop 0.496 m, tilt 1.20 deg) | pass (same) |
| 2 p / q / r | none sustained (max rms 1.56 / 1.58 / 0.05 dps) | none sustained (same) |
| 3 steady | pass (h_rms 0.0215 m ungated; roll/pitch -0.01/0.05 deg) | pass (same) |
| G4 chatter, 4 motors | sustained: 50.25 Hz (7 windows at 23 s) and 33.25 Hz (8 windows at 31 s), ratio 2.8e3-3.2e3 | sustained: 33.25 Hz, 15 flagged windows, ratio 2.8e3-3.3e3 |
| overall G3 | PASS | PASS |

Cause of the reported disagreement: the G3 verdicts and item values agree. The only difference is reporting: key 2 prints one line per motor (the max-RMS window, 33.25 Hz) while key 1 lists both lines. Both count the same 15 flagged windows and both say chatter is sustained. Chatter is G4, not part of the G3 pass, so it does not change the 16 verdict.

Verdict: PASS for G3 item 1/2/3 on run 16 (both keys). Chatter sustained (G4) on both keys.

## Unverified
- Exact ulog-time mapping of key 1's flagged windows (inferred from grid start and key 2 skip list).
- Whether the Q15 skip belongs to G3 item 2 (GATES.md 555 vs 607).
- Key 1 run locally failed (no scipy); re-run via `indi_project/docker/run.sh -n recon189k1b`.
- Chatter RMS floor for the 16 lines not checked against the 5e-4 threshold.
