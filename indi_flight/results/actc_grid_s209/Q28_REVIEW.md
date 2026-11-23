# Q28 independent review (S211, 2026-11-23, read-only reviewer agent)
Proposal reviewed: option A (MC_INDI_ACT_TC = median over motors of tau_sym; G3 box r uniform [0.88, 1.02] x tau_mean,
tau_mean = (tau_up + tau_down) / 2), keep the box, correct the wording; reject B and C.

Verdicts: A AGREE WITH CHANGES (wording); keep [0.88, 1.02] AGREE; reject B and C AGREE.

Recomputed from GRID_inst0.tsv (python3 -I, csv.DictReader; est_sym / true_mean matches sym_over_mean to 5e-5):
- r_mean (median of 4 motors), instance 0: asym 1 0.9990..1.0039; asym 3 down-slow 0.8983..0.9748; 3 up-slow 0.9327..0.9851.
- Cells above 1: four, all asym 1 (t0.5_d0 1.0021, t0.5_d10 1.0039, t1_d10 1.0016, t2_d10 1.0015). Truth instance
  (GRID.tsv) max 1.0021: the source of the "+0.2 %" in Q28.
- Per motor (ident_inst0.json): 0.843..1.040; 1.040 on t2_a3u_d10f3 (motors 0, 3 at 0.885; motors 1, 2 at 1.040).
  The roll injector splits motors by diagonal pair; the median of 4 is the mean of the two pairs.
- Seed-repeat spread of tau_sym on the 4 repeated cells: -0.5 / +0.7 / -1.5 / +2.0 %.
- Box edges: upper 1.02 = measured max 1.0039 + 1.6 % (not + 2 %); lower 0.8983 x 0.98 = 0.880.
- Margins, box_margins.py with r in {0.88, 1.02, 1.03, 1.05} instead of {0.88, 1.0, 1.02, fixed}, 800 Hz
  (box_margins_r_upper.tsv): worst corners identical at r 1.02, 1.03, 1.05 (rate 30.6 deg / 3.4 dB / 10.4 ms;
  rate+att 24.5 deg / 3.2 dB at r >= 1.02, 19.9 deg at r 0.88). At m 0.5-1, 1.02 -> 1.05 moves < 1 deg, < 0.1 dB.
  Q28's quoted numbers match BOX_MARGINS.md.
- Rejecting C: DECISIONS D-OWNER-Q27, 283 fails item 2 at ACT_TC x1.5 and x2, passes at x1; at asym 3 tau_slow = 1.5 tau_mean.

Findings (most severe first):
1. Q28 and D-ACTC-RULE quoted truth-instance numbers (<= 0.2 % high, 3.7 %, +1.75 ms); instance 0 gives 1.0039, 3.9 %,
   +2.9 / +6.7 ms. Corrected S211.
2. The bound holds for the median of 4 only (per motor 0.843..1.040); another injector axis or frame could move the split.
3. The 2 % allowance equals the largest seed spread seen (2.0 %, 4 pairs): no slack. One seed, roll injector, speed 4.
4. The linear model is flat in r from 1.02 to 1.05 and missed 283 (3 dB optimism): the upper edge rests on flight
   evidence (283 at x1.5, x2) only. "B margins nearly the same" is uninformative.
5. delay_hat on instance 0 includes telemetry delay: never feed it to a delay parameter.
