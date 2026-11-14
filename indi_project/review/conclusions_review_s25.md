# Review of report chapters 8-10 against their sources (session 25)

Scope: `report/08_results.md`, `09_discussion.md`, `10_conclusion.md` checked against
`results/acceptance_s15.md`, `heldout_s14.md`, `heldout_s15.md`, `heldout_h5_s15.md`,
`t8_motor_loss_s13.md`, `act_tc_sweep_s17.md`, `tuning/r4f.md`, `tuning/r2.md`, `tuning/r4.md`,
`speedcheck_indi_s22.md`, `review/control_law_review_s16.md`, `bench/scenarios.md` section 6.
Only real problems are listed. Numbers not listed below were checked and match.

## Chapter 8

1. **should-fix** `report/08_results.md:63` and `:24,:108`. Figure 8.1 caption says T8 was recorded on
   "all 10 recorded seeds" and `results/runs/motor_loss_0/{pid_default,indi_tuned}/seed1..seed10` exist on
   disk, but 8.1 and 8.3 state "T8 motor loss was flown with 3 seeds only ... so no significance test is
   possible". Either the 10-seed T8 data exist and the tables, 8.8 (n = 3) and 9.4 ("T8 has only 3 seeds and
   no test") are stale, or the figure uses unvetted runs. Resolve one way; if the 10 seeds are valid, run
   `summarize_seeds.py` on them and replace the 3-seed T8 rows.
2. **should-fix** `report/08_results.md:57`. "27-84 % lower attitude RMS on H2, H3 and T6-T8" (copied from
   `acceptance_s15.md:29`) is wrong for T8 as a whole: T8 whole-window rotation RMS is 1.14x PID (worse,
   `t8_motor_loss_s13.md`); only the fault-window attitude RMS is lower (0.197 vs 1.12 deg, 3 seeds).
   Replace with: "27-84 % lower attitude RMS on H2, H3, T6 and T7, and 5.7x lower in the T8 fault window
   (3 seeds; T8 whole-window RMS is 14 % worse because of the yaw step)".
3. **should-fix** `report/08_results.md:144,:294`. T1's primary metric is position RMS and 8.4 says the
   10-seed value "is not reported in the source files"; the summary table nevertheless gives T1 the verdict
   "INDI better (attitude)" on a secondary metric. This reads as favouring INDI. Replace the verdict cell
   with "no primary-metric result (position RMS noise-dominated); attitude RMS 0.76x, secondary; effort 1.04x".
4. **minor** `report/08_results.md:61,:75` vs `10_conclusion.md:13`. 8.3 correctly labels T9 "a plant-mismatch
   scenario rather than a disturbance", but 10.2 counts T9 (0.88) among "every disturbance scenario". Keep
   T9 out of the disturbance claim in ch. 10 (see item 12).
5. **minor** `report/08_results.md:106`. The per-scenario 5-seed ratios (gust_diag 0.57x, gust_x 0.61x,
   payload_add 0.75x) are not in `heldout_s14.md` "Reading" (which gives only the range 0.15-0.75x); they come
   from `STATE.md:89`. Cite `STATE.md` session 14 instead of `heldout_s14.md`.

## Chapter 9

6. **should-fix** `report/09_discussion.md:25`. "for the H5 plant this band is 5-9 Hz, which is the observed
   oscillation band". With tau_e = 0.0114 s and tau_t = 0.025/0.05 s, f* = 1/(2 pi sqrt(tau_e tau_t)) is
   9.4 Hz (up) and 6.7 Hz (down), so the predicted band is 6.7-9.4 Hz and only partly overlaps the observed
   5.2-6.5 Hz. The review's "5-9 Hz" (`control_law_review_s16.md:204`) was computed for plant pairs 12.5/25
   and 25/50 ms against each other, not against the frozen 11.4 ms model; its summary line 272 says 5-7 Hz.
   Replace with: "for the H5 plant and the frozen model this puts f* at about 6.7-9.4 Hz, close to but
   somewhat above the observed 5-7 Hz, which the added actuator phase lag may explain". Likewise "puts f* near
   14 Hz" (line 25) is the review's number for tau_e = 6.7 ms vs 20 ms, not for the sweep's f = 0.33 on the
   stock plant (f* about 16-23 Hz); say "well above crossover" rather than quoting 14 Hz.
7. **should-fix** `report/09_discussion.md:59`. "Only INDI is sensitive to the speed factor" overstates the
   PID check: `speedcheck_indi_s22.md:21-22` records PID step_roll attitude RMS moving -2.5 % between speed 4
   and 1 (`speedcheck_pid_default.md`); only on H6 is PID within 0.2 %. Replace with "On H6 only INDI is
   sensitive to the speed factor (PID moved 2.5 % on step_roll in the earlier check)".
8. **minor** `report/09_discussion.md:21`. "It is also the reason the verdict is a loss" — criterion 1 also
   fails independently on H4 (as 8.2, 9.1 and 10.1 say). Say "it is sufficient on its own for the verdict".
9. **minor** `report/09_discussion.md:15`. "roll steps are 12 % better and yaw steps 10 % worse" omits that
   these are 3-seed tuning-set numbers (`r4f.md`), which 8.4 correctly says are not evidence of
   generalisation. Add "(tuning set, 3 seeds)".

## Chapter 10

10. **must-fix** `report/10_conclusion.md:21`. "searched over 64 candidates" contradicts the sources and the
    rest of the report: 40 candidates (24 in r1 + 16 in r2; `results/tuning/r2.md:19-25`, `summary.csv`
    row counts 24 and 16; `08_results.md:14`, `09_discussion.md:63`). Replace "64" with "40".
11. **should-fix** `report/10_conclusion.md:21`. "defaults that were confirmed, not assumed" overclaims what
    9.4 concedes: random sampling in a 12-D box "shows that the defaults are hard to beat that way, not that
    they are optimal", and the ~2 % run-to-run noise is larger than the 0.6 % gap (`r2.md:18`). Replace with
    "defaults that a 40-candidate random search did not beat; this shows they are hard to improve by
    sampling, not that they are optimal".
12. **should-fix** `report/10_conclusion.md:13`. Heading "Disturbance rejection is better on every disturbance
    scenario" is stronger than the data: T9 is a plant mismatch (8.3), and on T8 INDI is better only in the
    fault window while the whole-window rotation RMS is 14 % worse (3 seeds, no test). Replace with
    "Attitude disturbance rejection is better on all four disturbance scenarios (T6, T7, H2, H3) and at T8
    fault onset" and move T9 to a separate sentence on plant mismatch.
13. **should-fix** `report/10_conclusion.md:25`. "The control-law review found that a model slower than the
    plant amounts to a gain reduction and is safe" states as a finding what 9.2 presents as "an analysis,
    not a measured loop transfer function ... the most likely mechanism". Replace "found ... is safe" with
    "argues ... should be benign, which the post-acceptance sweep on the stock plant (f = 1.5-3, 3 seeds)
    is consistent with".
14. **should-fix** `report/10_conclusion.md:27`. "This is why the weakness is an actuator-model problem and
    not a gain-tuning problem" was not tested: `heldout_h5_s15.md:72` says a lower K_R "is a design trade not
    yet evaluated", and the limit cycle is reported "at the frozen K_R 23.9". The sweep shows a mis-set
    ACT_TC on the stock plant is benign, not that gains are irrelevant. Replace with "The sensitivity is to
    an actuator slower than modelled; whether lower gains would buy tolerance to it was not evaluated".
15. **minor** `report/10_conclusion.md:27`. "A later sweep" should be labelled as in 9.2: "A post-acceptance
    sweep (session 17, not part of the frozen result)".
16. **minor** `report/10_conclusion.md:9` and `09_discussion.md:15`. "The result is not evidence that INDI is
    the worse controller on average" is defensible, but given yaw (1.31x), T5 peak deviation (1.08x), H5
    effort (3.08x) and T8 saturation, add the symmetric clause already present in 8.8: "nor that it is the
    better one".

## Checked and found consistent (no action)

Criteria table and per-H table in 8.2; all 8.3, 8.5, 8.6, 8.7 table values against `heldout_s14.md`,
`heldout_h5_s15.md`, `heldout_s15.md`; T8 ratios and 0.18 derivation; r4f ratios and effort ranges; r4 yaw
frontier (0.98 at 3.8x, c10 1.089 at 1.13-1.14); ACT_TC sweep range 0.129-0.161; speed-check ratios
0.874-0.904 / 0.881-0.973; p-value floors for n = 10, 5, 3; the post-hoc rule changes (averaging H5 parts
still fails criterion 3; excluding H4 does not rescue it); post-acceptance work in 9.2, 9.4 is labelled.
The verdict "INDI does not outperform PID" is stated unchanged in 8.2, 8.8, 9 (intro, 9.1), 10.1.
