# V' verdict for indi_v3 (session 47)

V' = `bench/scenarios.md` sec. 9 (frozen, D-heldout-v3), 5 entries x seeds 1-10 x {pid_default, pid_tuned, indi_v2,
indi_v3}, flown by `bench/vprime.sh` 00:56-01:25 on 2026-11-15 (200 flights, the four controllers of an (entry, seed)
side by side). indi_v3 frozen before V' flew (`bench/params/indi_v3.params`, D-v3-freeze). Watchdog on (O-12):
aborted runs are failures and were not re-flown. No host suspend in the journal; `bench/glitch_scan.py` found no
estimator glitch (it skips the 52 aborted runs, which have no window end). W1/W2 metric: tilt RMS (D-vprime-metric).
Tables from `python3 bench/s2_verdict.py results/vprime/runs --vprime --final --b <controller>`.

## indi_v3 vs pid_tuned (the verdict)

4. hover effort (T1, v2 configuration, 5 seeds, `results/v3_hover_effort.md`): 2.14x pid_tuned (needs <= 1.5).

**Outcome: INDI does not outperform PID** (criteria 1, 2 and 4 fail; criterion 3 met: indi_v3 is not worse than
pid_tuned on any entry).

## Post-hoc (not part of the verdict)

indi_v2 vs pid_tuned:


pid_default vs pid_tuned:


Failures per controller (watchdog trips, all "> 3 m below hold altitude for 1 s"): W1 vp_loss1_06 10/10 for every
controller; W4 vp_sag75_att pid_default 7, pid_tuned 6, indi_v2 3, indi_v3 6 of 10; W2, W3, W5 none.

## Reading
- **v3 does what it was built for.** v2's actuator-gap weakness is gone: on W2 (motor 2 at 0.8) v2 is 9.1x pid_tuned in
  tilt, v3 0.95x (better on 10/10 seeds, by 5 %); on W3 and W5 v2 is 2.7x and 1.9x, v3 1.01x and 0.99x.
- **v3 matches the tuned PID, it does not beat it.** Every completed entry is within 5 % of pid_tuned; two are
  significant but below the 10 % bar. The disturbance-rejection margin of v1 (section 8) does not appear on these
  actuator-fault entries, where both controllers are limited by the remaining thrust, not by the loop.
- **W1 and W4 exceed the vehicle, not a controller.** Every controller loses altitude under W1 (motor 1 at 0.6 thrust,
  hover throttle ~0.59) and about half the runs under W4 (75 % thrust). These entries were never flown before V'
  (only W3/W5 were harness-checked), so their severity was not calibrated; that is a design flaw of V', recorded here
  rather than repaired after the fact. A watchdog-off diagnostic of W1 (post-hoc) is the next step.
- indi_v2 has fewer W4 trips (3 vs 6) but 2-9x worse attitude wherever it survives the gap entries.
