# V' verdict for indi_v3 (session 47)

V' = `bench/scenarios.md` sec. 9 (frozen, D-heldout-v3), 5 entries x seeds 1-10 x {pid_default, pid_tuned, indi_v2,
indi_v3}, flown by `bench/vprime.sh` 00:56-01:25 on 2026-11-15 (200 flights, the four controllers of an (entry, seed)
side by side). indi_v3 frozen before V' flew (`bench/params/indi_v3.params`, D-v3-freeze). Watchdog on (O-12):
aborted runs are failures and were not re-flown. No host suspend in the journal; `bench/glitch_scan.py` found no
estimator glitch (it skips the 52 aborted runs, which have no window end). W1/W2 metric: tilt RMS (D-vprime-metric).
Tables from `python3 bench/s2_verdict.py results/vprime/runs --vprime --final --b <controller>`.

## indi_v3 vs pid_tuned (the verdict)

| entry | primary metric | pid_tuned mean | indi_v3 mean | ratio | b<a | med impr | p | effort ratio | fails pid_tuned/indi_v3 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| vp_loss1_06 | attitude_tracking.tilt_rms_deg | - | - | - | - | - | - | - | 10/10 | no data |
| vp_loss2_08 | attitude_tracking.tilt_rms_deg | 0.7771 | 0.7362 | 0.95 | 10/10 | 5 % | 0.00195 | 0.78 | 0/0 | better < 10 % |
| vp_gain03_att | attitude_tracking.roll_rms_deg | 2.966 | 2.987 | 1.01 | 6/10 | 0 % | 0.846 | 1.16 | 0/0 | n.s. |
| vp_sag75_att | attitude_tracking.roll_rms_deg | 3.099 | 2.99 | 0.96 | 2/3 | 1 % | 0.75 | 1.00 | 6/6 | n.s. |
| vp_tau2_loss2_att | attitude_tracking.roll_rms_deg | 3.164 | 3.12 | 0.99 | 8/10 | 1 % | 0.0488 | 1.17 | 0/0 | better < 10 % |
Complete entries (10 paired seeds): 3/5
1. INDI failures in V': 16 ['vp_loss1_06/seed1', 'vp_loss1_06/seed2', 'vp_loss1_06/seed3', 'vp_loss1_06/seed4', 'vp_loss1_06/seed5', 'vp_loss1_06/seed6', 'vp_loss1_06/seed7', 'vp_loss1_06/seed8', 'vp_loss1_06/seed9', 'vp_loss1_06/seed10', 'vp_sag75_att/seed1', 'vp_sag75_att/seed2', 'vp_sag75_att/seed5', 'vp_sag75_att/seed8', 'vp_sag75_att/seed9', 'vp_sag75_att/seed10'] (seen/T entries: see the seen set)
2. significantly better (>= 10 %, p < 0.05): 0/5 (needs >= 4)
3. significantly worse by > 10 %: 0 (needs 0)
Outcome on criteria 1-3 (V' only; criterion 1 also needs the seen/T entries, criterion 4 hover): INDI does not outperform PID
4. hover effort (T1, v2 configuration, 5 seeds, `results/v3_hover_effort.md`): 2.14x pid_tuned (needs <= 1.5).

**Outcome: INDI does not outperform PID** (criteria 1, 2 and 4 fail; criterion 3 met: indi_v3 is not worse than
pid_tuned on any entry).

## Post-hoc (not part of the verdict)

indi_v2 vs pid_tuned:

| entry | primary metric | pid_tuned mean | indi_v2 mean | ratio | b<a | med impr | p | effort ratio | fails pid_tuned/indi_v2 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| vp_loss1_06 | attitude_tracking.tilt_rms_deg | - | - | - | - | - | - | - | 10/10 | no data |
| vp_loss2_08 | attitude_tracking.tilt_rms_deg | 0.7771 | 7.042 | 9.06 | 0/10 | -806 % | 0.00195 | 0.58 | 0/0 | **worse** |
| vp_gain03_att | attitude_tracking.roll_rms_deg | 2.966 | 8.036 | 2.71 | 0/10 | -170 % | 0.00195 | 0.81 | 0/0 | **worse** |
| vp_sag75_att | attitude_tracking.roll_rms_deg | 3.012 | 2.855 | 0.95 | 1/5 | -10 % | 0.625 | 0.49 | 6/3 | n.s. |
| vp_tau2_loss2_att | attitude_tracking.roll_rms_deg | 3.164 | 6.112 | 1.93 | 0/10 | -92 % | 0.00195 | 0.74 | 0/0 | **worse** |

pid_default vs pid_tuned:

| entry | primary metric | pid_tuned mean | pid_default mean | ratio | b<a | med impr | p | effort ratio | fails pid_tuned/pid_default | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| vp_loss1_06 | attitude_tracking.tilt_rms_deg | - | - | - | - | - | - | - | 10/10 | no data |
| vp_loss2_08 | attitude_tracking.tilt_rms_deg | 0.7771 | 0.9612 | 1.24 | 0/10 | -24 % | 0.00195 | 0.53 | 0/0 | **worse** |
| vp_gain03_att | attitude_tracking.roll_rms_deg | 2.966 | 3.394 | 1.14 | 0/10 | -10 % | 0.00195 | 0.81 | 0/0 | worse < 10 % |
| vp_sag75_att | attitude_tracking.roll_rms_deg | 2.882 | 3.419 | 1.19 | 0/3 | -12 % | 0.25 | 0.58 | 6/7 | n.s. |
| vp_tau2_loss2_att | attitude_tracking.roll_rms_deg | 3.164 | 3.486 | 1.10 | 0/10 | -11 % | 0.00195 | 0.80 | 0/0 | **worse** |

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
