# Acceptance check against `bench/scenarios.md` section 6 (session 15)

All six held-out scenarios flown with 10 paired seeds each, frozen candidates (D-freeze). `pid_tuned` = PX4 defaults
(no retuned candidate beat them in r1+r2, `results/tuning/r2.md`). Sources: `results/heldout_s14.md` (H2, H3, H6),
`results/heldout_h5_s15.md` (H5), `results/heldout_s15.md` (H1, H4).

| H | primary metric | INDI / PID | median impr. | p | verdict |
|---|---|---|---|---|---|
| H1 traj_circle_fast | position RMS | 0.73 | ~27 % | 0.002 | better (path infeasible for both, D-h5) |
| H2 gust_diag | attitude RMS | - | 44 % | 0.002 | better |
| H3 com_shift | attitude RMS | - | 84 % | 0.002 | better |
| H4 motor_loss_2 | position RMS | 1.15 | - | 0.11 | not significant; both crash 10/10 |
| H5 mismatch_combined, T2 part | stepped-axis attitude RMS | 0.91 | 10 % | 0.002 | borderline better, but with a 5-7 Hz limit cycle |
| H5 mismatch_combined, T4 part | roll-rate RMS during pulses | 1.58 | -58 % | 0.002 | **significantly worse** |
| H6 step_diag | stepped-axis attitude RMS | ~0.9 | 10 % | 0.002 | borderline better (exactly at threshold) |

1. No INDI run fails: **not met.** INDI crashes on H4 on 10/10 seeds. PID crashes on 10/10 too and the two behave
   alike up to impact, but the criterion is stated for INDI alone and is applied as written.
2. Better on >= 4 of 6 H: met (H1, H2, H3 clearly; H6 and the T2 part of H5 at the 10 % threshold).
3. Not significantly worse by > 10 % on any H: **not met** (H5, rate pulses 1.58x; root cause actuator-model
   mismatch, `heldout_h5_s15.md`).
4. Hover effort <= 1.5x: **met.** T1 hover, 10 paired seeds (`results/hover_s15.log`, `summarize_seeds.py results/runs
   hover`): motor-rate RMS 0.0387 vs 0.0371 /s (1.04x, p 0.16); attitude RMS 0.76x (10/10, p 0.002). PID seeds 1-3
   were re-flown by the hover batch (same defaults); seeds 4-10 come from earlier sessions.

**Outcome under the frozen rules: "INDI does not outperform PID".** Criterion 3 fails on its own (H5), and
criterion 1 fails on H4. Even setting H4 aside as infeasible for both controllers, the outcome is unchanged.

What the data do show: INDI is much better at rejecting disturbance torques (H2, H3, T6-T8: 27-84 % lower attitude
RMS) and slightly better at tracking, but it is fragile to an error in its actuator model (motor time constant x2
-> limit cycle), which PID tolerates. That trade-off is the main result for the report.
