# Questions to the owner

No open question (S50). Q1-Q4 closed, archived in JOURNAL.md.

N1 closed S61 (moved to JOURNAL.md; open items C2, C3 carried in STATE.md).

N2 closed S69 (summary in JOURNAL.md).

Q5 closed S70 (no owner objection to addendum 6; summary in JOURNAL.md).

Q6 closed S120 (owner answer B, conditions (i)-(v) in DECISIONS.md D-IDENT; full text in JOURNAL.md).

Owner directive 2026-11-20 (F-7/F-8/F-9) closed S134: acted on (DECISIONS D-F7-GROUND, GATES 5b, STATE
next actions); text in JOURNAL.md.

Q7 closed S140 (owner answer A: G5.7 validity at the 4 edges leaving posctl; written into GATES 5b; text in JOURNAL.md).

Q8-Q15 and the owner note of 2026-11-21 closed S175 (answers acted on: GATES.md "Owner amendments S175",
DECISIONS D-OWNER-Q8-Q15 and D-JFF-KEEP; full text in JOURNAL.md S175).

Q16 closed S178 (owner answer A: G2 PASSED once the freeze-7 outer cells and 2 rate/att spot-check cells pass;
3 rate x-check groups reported as evidence limit, A-51 open; full text in JOURNAL.md S178).

Q17 and Q18 closed S180 (owner answers A; GATES "Owner amendments S180", D-OWNER-Q17-Q18; text in JOURNAL.md).

## Owner note (2026-11-21, after Q17): stay inside INDI scope
1. Scope line. A behaviour that the PID reference shows too (same scenario and seed, same signature in the gate
   metric) is a PX4 fact, not INDI work: report both stacks' values and, if it blocks a gate row, write the owner
   question. Do not chase or fix stock PX4 code (EKF2, mc_pos_control, land detector, commander) or simulator
   plumbing beyond the injectors that the gate factor tables require. No new hook without a gate row that consumes it.
2. G3 tel_frozen hook. Keep it, since the G3 factor table and C5 list frozen telemetry, but build the simplest injector
   (one session, two keys). If it does not fly after that session, stop and write an owner question proposing to drop
   the frozen factor from G3 instead of continuing the plumbing.
3. G4 chatter keys. Before any F2 firmware work, reconcile key 1 (88.5 Hz) and key 2 (33.5 Hz) on the same
   cruise_typ_s1 lemniscate window (results/g55_gain_probe_s179). F2 targets only a line that both keys agree on.
   One sonnet task, existing scripts.
4. G4 item 3 in the XY_P 1.2 probe (altitude_mean 0.29 m, limit 0.1). Look up the freeze-7 value and fly the PID
   reference before any cause search (point 1 applies).

S180: points 3 and 4 acted on (results/g55_gain_probe_s179/RECONCILE_S180.md: keys agree on 33.5 and 89.25 Hz;
cruise item 3 offset equals PID, not a G4 row). Points 1-2 stand as rules (point 2 in STATE next action 4).

Q19 closed S183 (owner answer A with PID guard; GATES "Owner amendment S183", D-OWNER-Q19; text in JOURNAL.md S183).

Q20, Q21, Q22 closed S187 (owner answers acted on: GATES "Owner amendments S187", DECISIONS D-OWNER-Q20-Q22; full
text in JOURNAL.md S187).

Q23 closed S191 (owner answer B: full revert of aa4fd2654a, D-JFF-KEEP overturned for it; DECISIONS
D-OWNER-Q23; full text in JOURNAL.md S191).

Q24 and Q25 closed S197 (owner answers B and B: GATES "Owner amendments S197", D-OWNER-Q24, D-OWNER-Q25,
design/airframe_requirements.md; full text in JOURNAL.md S197).

Q26 closed S207 (owner answer: check first, C not chosen; items 1-4 done, results and recommendation in Q27;
full text in JOURNAL.md S207).

Q27 closed S208 (owner answer: identify ACT_TC first, no box change now; acted on in GATES "Owner amendments S208",
DECISIONS D-OWNER-Q27; full text in JOURNAL.md S208).

## Q28 (S209, 2026-11-23): G3 controller-ACT_TC box and ACT_TC rule from the measured identification bound. BLOCKING for G3 (test definition) and for G6 item 7 ordering
Context (Q27 item 1, GATES 6c):
- Estimator `bench/ident_actc.py` (two keys; off-grid delay fix 2dd2110a0c) flown on the 30-cell grid of 6c
  (`results/actc_grid_s209/README.md`): plant tau_slow x0.5..3 of 33 ms, asym 1 / 3 down-slow / 3 up-slow, delay 0 / 10 ms.
- 0/30 failed identifications. Per motor tau_up and tau_down within 3.7 %; delay recovered within 0.1 ms (+1.75 ms offset).
- The single tau the firmware takes (symmetric fit tau_sym) returns a mean, never tau_slow: tau_sym / tau_mean = 0.996-1.002
  (asym 1), 0.90-0.98 (asym 3); tau_sym / tau_slow = 0.60-0.66 at asym 3. It never exceeds tau_mean by more than 0.2 %.
- Limits: telemetry frames 0-3 NOT applied (simulator hook inert, A-59; the 10 ms delay cells cover more delay than
  3 frames); one seed except 4 corners; roll injector only; sim speed 4.
- Model margins at the box corners (`results/actc_grid_s209/BOX_MARGINS.md`, same method as Q27, 800 Hz, worst over
  G1 x0.8/1.2): proposed box rate 30.6 deg / 3.4 dB / 10.4 ms, rate+att 19.9 deg / 3.2 dB (corner tau_mean x3, 10 ms,
  asym 3); fixed 0.033 (freeze-10 campaign) rate+att UNSTABLE at the same corner. Symmetric plants: box rate+att 32 deg
  vs fixed 5.7 deg. Below G2's 45 deg / 6 dB at the slow + 10 ms corners: reported as a limit per Q27 item 3.
Options:
- A (recommended). Rule: MC_INDI_ACT_TC = median over motors of the identified tau_sym, no rounding, no cap (the
  estimator never errs high; 283 showed erring high is the harmful side). G3 box: controller ACT_TC = r x plant tau_mean,
  r drawn uniform [0.88, 1.02] (measured 0.90-1.00 plus 2 % estimator error each side), independent of the other draws.
- B. Same rule, r drawn from the asymmetry-dependent measured relation (r = 1 at asym 1, 0.90-0.98 at asym 3) plus
  +-4 %. Closer to reality, harder to explain; margins nearly the same.
- C. Rule ACT_TC = identified tau_slow (from tau_up/tau_down). Matches the slow motor but the controller then runs
  above the mean on asymmetric motors, the side 283 failed on.
Meanwhile (not decided by this question): fix the telemetry-latency hook (A-59, one session, simplest injector, two
keys; if it does not fly after that session, I ask to drop the frames factor), and G7 unit 8. No G3 or G6 item-7 flight.
Blocked: G3 re-fly and G6 item 7 only.
CORRECTION S209 (same session, before any answer): `ident_actc.py:275` reads the highest esc_status instance, which in
SITL is the simulator's TRUE rotor speed (gz_bridge truth publisher), not the telemetry instance 0 a vehicle has. The
grid numbers above therefore measure the fit on true rotor speed: they are a best case, not the bound. Do not answer
from them yet. Next session: fit instance 0 on the same 30 logs (no flight), re-table, re-run box margins, and update
this question. This also explains A-59 (the delayed telemetry was never fitted).
RESOLVED S209: refit on telemetry instance 0 (results/actc_grid_s209/REFIT_INST0.md, --esc-instance 0 now default):
0/30 failed, tau_up/down <= 3.9 %, r_mean 0.898-1.004 (each bound within 0.003 of the truth fit), frames 3 seen
(+3.8 ms delay). Box r [0.88, 1.02] and BOX_MARGINS unchanged. Q28 stands as written above; A-59 closed (hook works).
CORRECTION S211 (independent review, results/actc_grid_s209/Q28_REVIEW.md): the box stands, the wording above does not.
On telemetry instance 0: tau_up/down <= 3.9 % (not 3.7); delay offset +2.9 ms at frames 0 and +6.7 ms at frames 3 (not
+1.75); tau_sym (median of 4 motors) reaches 1.0039 x tau_mean on symmetric plants, so "never exceeds tau_mean by more
than 0.2 %" and option A's "never errs high" are false: it errs high by up to 0.4 %. The upper edge 1.02 is the measured
max + 1.6 %, not + 2 %; the lower edge 0.8983 x 0.98 = 0.880 holds. Limits added: the bound holds for the median of 4
only (single motors 0.843-1.040, split by diagonal pair on the roll injector); the 2 % allowance equals the largest
seed spread seen (2.0 %, 4 pairs), no slack; the linear model is flat in r from 1.02 to 1.05
(box_margins_r_upper.tsv), so the upper edge rests on flight evidence only (283 fails at x1.5); delay_hat on instance 0
includes telemetry delay and is never fed to a delay parameter. Review verdicts: A agree with these changes, box
agree, B and C rejected.
