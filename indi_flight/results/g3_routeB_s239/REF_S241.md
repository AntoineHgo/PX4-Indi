# G3 route B draws 2 and 3: PID reference and INDI re-fly (S241)

Speed 1, binary 903eae63, seed 173 / n 300, draws checked equal to campaign run_002 / run_003 g3_draw.json. Scored with
`g3_chain.sh rescore` (key 1 g3_score.sh, key 2 g3_checks_key2.py). Campaign dir untouched. Raw logs untracked.
Item 2 = body-rate oscillation, item 4 = tracking (horiz RMS limit 0.5 m).

## Campaign reference (chain scores, for comparison)
- run_002 (INDI): items 1-3 P, item 4 FAIL 0.834 m on both keys. Chain column shows "-" (defect, S240).
- run_003 (INDI): item 2 FAIL on both keys (q at 2.0 Hz), item 4 FAIL 0.553 m on both keys.

## a) PID draw 2
- command: `timeout 1800 python3 indi_flight/results/g3_routeB_s239/ref_s241/fly_pid_ref.py 2` (pid_default, pid_base.params)
- flight ok (rc 0); output ref_s241/pid_d2/run_002
- key 1: items 1 P, 2 P (0 flagged windows, p/q/r not sustained), 3 P, 4 FAIL, 5 P, 6 n/a. Overall FAIL.
- key 2: items 1 P, 2 P (p/q/r not sustained), 3 P, 4 FAIL, 5 P, 6 n/a. Overall FAIL.
- item 4 horiz RMS: 0.862 m (key 1 = key 2), vert 0.089 m.

## b) PID draw 3
- command: `timeout 1800 python3 indi_flight/results/g3_routeB_s239/ref_s241/fly_pid_ref.py 3`
- flight ok (rc 0); output ref_s241/pid_d3/run_003
- key 1: items 1 P, 2 P (0 flagged windows on p/q/r), 3 P, 4 FAIL, 5 P, 6 n/a. Overall FAIL.
- key 2: items 1 P, 2 P (p/q/r not sustained), 3 P, 4 FAIL, 5 P, 6 n/a. Overall FAIL.
- item 4 horiz RMS: 0.917 m (key 1 = key 2), vert 0.063 m.

## c) INDI re-fly draw 3 (chain command, MC_INDI_POS_EN 1 from g5_freeze_s157/params.params)
- command: `indi_project/docker/run.sh -n g3c_s241_003 -t 1500 -- python3 indi_flight/bench/g3_run.py --seed 173 --n 300
  --start 3 --stop 3 --base-params indi_flight/results/g5_freeze_s157/params.params --out-root .../ref_s241/indi_d3
  --timeout-s 1200 --speed 1` (wrapped in `timeout 1800`)
- flight ok (rc 0, validity valid); output ref_s241/indi_d3/run_003
- key 1: items 1 P, 2 FAIL (q sustained, 10 flagged windows, 2.00 Hz lines at idx 49 and 57, 3 windows each), 3 P,
  4 FAIL (0.546 m), 5 P, 6 n/a. Overall FAIL.
- key 2: items 1 P, 2 FAIL (q sustained at [50.0, 2.0 Hz]), 3 P, 4 FAIL (0.546 m, vert 0.106 m), 5 P, 6 n/a. Overall FAIL.

## Verdict
- PID on draw 2 fails item 4 (0.862 m), the same item as INDI (0.834 m): same item, not INDI-only.
- PID on draw 3 does NOT fail item 2 (no 2 Hz q line), but fails item 4 (0.917 m), as INDI does (0.553 m): item 4 is not
  INDI-only; item 2 on draw 3 is INDI-only in this single flight pair.
- INDI draw 3 re-fly reproduces item 2 (q at 2 Hz, both keys) and item 4 (0.546 vs 0.553 m campaign).

## Flags (unverified or caveats)
- Single flight per arm; no spread estimate. Item 2 line frequency in the re-fly is 2.00 Hz only (campaign had 2.00 and 2.25 Hz).
- PID runs: base params carry no MC_INDI_*, so the INDI-only draw factors (g1_ctrl_mult) are NOT_APPLIED (as in ref264);
  the g3_run unapplied check was not run for PID (same as S224 pattern).
- Item 6 not applicable (position mode). Chain SCORES.tsv for the new dirs shows only items 1-3 (same defect).
- Scripts: ref_s241/fly_pid_ref.py (new, copy of the ref264 pattern); scoring via unmodified chain rescore.
