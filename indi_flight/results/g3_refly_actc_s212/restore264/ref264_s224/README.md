# Draw 264 PID reference (S225), run index 24, speed 1, binary 903eae63ceb1 (gate binary, not rebuilt)

Flown: (a) `q0_bld100/` INDI, MC_INDI_ACT_BLD 1.0 (S224, aborted by flight watchdog at sim t=61.48 s); (b) `pid_024/run_024` PID (`pid_default`), same draw (saturation 0.351, weak motor 3 at 0.709), flown by `fly_pid_run.py 24` (outcome ok, full flight, one flight, no retry; an earlier interrupted attempt was discarded).
Argv of (b) equals the C212 speed-4 run_024 and the INDI speed-1 re-fly except controller and speed (checked by the script, `pid_fly.txt`). Params: PID uses `g3_pretest_s187/pid_refs/pid_base.params` plus the draw overrides (no MC_INDI_* set), so the diff vs INDI is the controller and its own params.
Scoring: `g3_chain.sh rescore pid_024` (key 1 = g3_checks via g3_score.sh, key 2 = g3_checks_key2.py), `pid_024/SCORES.tsv`, `pid_024/key2/run_024.json`. Item 2 split pre/post fault: `analyze.sh` -> `analyze_out.txt`, `pid_024/split.json` (cut 45.07 s, ulog base, as in S223).

| | INDI tb 1.0 (q0) | INDI tb 0.10 | INDI tb 0.05 | PID |
|---|---|---|---|---|
| outcome | aborted (watchdog, 61.48 s) | ok | ok | ok |
| max tilt after fault [deg] | 66.8 (>60 from 59.87 s, run ends 61.49 s) | 48.5 | 47.9 | 40.9 (scorer 41.0) |
| key1 item 1 / 2 / 3 | INVALID | PASS / FAIL / FAIL | PASS / FAIL / FAIL | PASS / FAIL / PASS |
| key2 item 1 / 2 / 3 | INVALID | PASS / FAIL / FAIL | PASS / FAIL / FAIL | PASS / FAIL / PASS |
| item 3 horiz RMS (limit 0.30), key1 = key2 | - | 0.371 | 0.362 | 0.123 |

INDI tb 0.10 / 0.05 columns copied from `../blend264_s223/README.md` (they are INDI on the same draw and binary; tb = MC_INDI_ACT_BLD).
PID item 1: tilt >60 deg 0.0 s, height drop 0, excursion 1.57 m. Item 3 also: altitude mean -0.069 m (limit 0.2), window 62.2-65.2 s.

## PID item 2 (both keys)
- Whole run: FAIL on q only, one 2.0 Hz line, 3 windows, rms max 20.7 dps (key 1, from 42.5 s airborne-relative) / 19.0 dps (key 2, from 42.8 s). p and r not sustained.
- Split at the fault cut: pre-fault pass (max rms 2.5 dps), post-fault pass on both keys (max rms p 3.5, q 4.3, r 1.6 dps). The whole-run line therefore sits in windows straddling the cut (it starts 2.5 s before it, 4 s windows), not in a sustained post-fault oscillation. Same straddling appears in the INDI whole-run lines (from 42-43 s), but INDI also kept a post-fault 2 Hz p/q line (11-28 dps) that PID does not.
- Item 2 flagged by the official scorer on whole-run, so PID is recorded FAIL on both keys; that FAIL comes from the fault transient itself.

PID fails items 2/3 too: item 2 yes (whole-run scorer, straddling-window q 2 Hz line, no sustained post-fault line), item 3 no (0.123 m, passes).
Unverified: single flight, spread unknown; INDI tb 1.0 tilt from `scripts/tilt.py` (run ends at abort).
