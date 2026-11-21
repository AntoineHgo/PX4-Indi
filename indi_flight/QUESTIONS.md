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

## Q20 (S184, 2026-11-21): which RMS does the Q19 PID guard compare? BLOCKING for G4 (guard rows)
Context: the S183 amendment says a G4 row FAILS "if the INDI line RMS in a skipped window exceeds the PID reference at
the same transition". The second key (`results/freeze9_s183/g4/Q19_KEY2_REVIEW.md`, F1) finds the metric undefined:
which windows, which line, any floor or tolerance. Freeze-9 G4 is NOT PASSED under both readings (GATES "G4 verdict at
freeze-9"), so this question does not change today's verdict; it sets the target of the fix and of the re-score.
- Reading A (flagged line): compare only lines above the chatter floor 5e-4 (the G3 detector's own flag). INDI fails
  where it is flagged and PID is not, or both are flagged and INDI > PID. Freeze-9: 5 of 16 transitions fail (INDI
  20.0-20.8 Hz 5.0-5.3e-4, PID 2.7-4.4e-4).
- Reading B (any window): max line RMS over all overlapping windows, strict INDI > PID, no floor. Freeze-9: 9 of 12
  fail, several at levels far below the 5e-4 floor, i.e. noise-level comparisons between two stacks (lesson 6).
Recommendation: A (absolute floor, then the PID comparison only where the floor is crossed).
Meanwhile: one session of cause search on the INDI 20 Hz transition line (log analysis, no firmware change), which
both readings require. Not blocked on other gates (G5.10 set-up continues). No re-score of guard rows until answered.
Added S184 after the cause search (`results/g4_20hz_cause_s184/README.md`, script line20.py with self-test):
- 17->4 (take-off -> loiter): a physical 20 Hz roll/pitch transient (truth body rate 1.5e-3 rad/s, torque x/y, all 4
  motors differential), onset at the end of the take-off setpoint stream, decays ~5x within 10 s. PID shows the same
  onset and shape at 0.5-0.65x the INDI amplitude (PID motor line 2.8-4.1e-4, INDI up to 5.3e-4). The 1.5-1.9x INDI
  amplification is shown; its cause (rate-loop gain near 20 Hz) is a hypothesis.
- 14->18 (offboard -> land): no tone in 19.5-21 Hz in either stack (both at floor); the guard's 5e-4 flag there comes
  from its +-2 Hz integration on broadband descent energy, i.e. a guard artefact under both readings.
So this is partly a PX4 fact (owner note point 1): the transient exists in both stacks, INDI amplifies it ~1.7x at a
level 0.05 % of full motor command. Options: A strict (Reading A; 17->4 fails; next = identify the 20 Hz amplification
from the G2 rate-loop data, then a firmware change that re-opens G2/G4/G5); C (Reading A, and a transition transient
that PID also shows is reported with both values, failing only above an absolute bound you set). Recommendation: A with
a narrow-band (+-0.5 Hz) line measure that removes the 14->18 artefact; I will not propose a tolerance myself.

## Q21 (S185, 2026-11-21): G5.10 SAT part, the "hover needs >= 1.0 command" set-up cannot be reached. BLOCKING for G5.10 (and so the G5 verdict)
Context: Q9(c) defines the SAT part at a thrust scale where hover needs >= 1.0 command, entered from a pinned hover.
- Step-in 1 -> 0.136 with the 3 m step (S181): an 86 % thrust-loss test, both stacks hit the ground (D-G510-SAT-SETUP).
- Ramped scale-down during hover (S184, results/g510_setup_s184/README.md, 4 ramp shapes, INDI and PID): both stacks
  sink once the scale passes ~0.2 (hover cmd ~0.65-0.8), before the window opens; PID run s1 alt loss 2.39 m, INVALID.
  Log: rotor speed stays at hover (thrust = weight) while the vehicle sinks 0.4-0.5 m/s: a ramp-disturbance velocity
  error, not a plant limit (T/W 1.08 at the final scale was real). `hover_thrust_estimate` stuck at 0.337 while the
  true hover command rises (hypothesis for the low vertical gain, stock PX4, not chased: owner note point 1).
- This meets the overturn rule of D-G510-SAT-SETUP (PID fails too) and the row text needs a change: your call.
Options:
  A. Demand transient at a moderate scale (0.3-0.4, hover cmd ~0.6): 3 m climb step + full-throttle demand saturates
     all motors >= 0.99 for >= 1 s (scored on the motors), limits unchanged (alt loss 2.0 m, tilt, 5 s recovery). The
     "pinned hover" wording is dropped. Recommended: tests windup and saturation handling, reachable by both stacks.
  B. Keep the pinned hover and add the hover-estimate fix to the flight params (MPC_THR_HOVER near the true hover at
     the low scale): changes the stock hover set-up for this row only.
  C. Drop the SAT part; G5.10 = the stabilized full-scale part (Q17 A) only, reported as such.
Meanwhile: no G5.10 flight or score. Work moves to G3 set-up (tel_frozen hook, STATE next action 4). Blocked on G5 verdict.

## Q22 (S186, 2026-11-21): G3 pre-test oscillations sit outside the attitude-loop stability boundary; box or gains? BLOCKING for G3
Context (results/g3_pretest_s173/run_017/LOC_CAUSE_S186.md, results/g3_osc_margin_s186/README.md, results/g3_excursion_s186/RESCORE_V2.md):
- Fixed two G3 checker defects (both keys agree): excursion now vs the time-matched setpoint (old rule measured the 5 m lemniscate),
  and the G4 chatter line no longer decides G3 item 2 (GATES 304). Remaining pre-test failures: sustained 1.6-2 Hz roll/pitch limit
  cycle in runs 03, 07, 13, 17 (17 tumbles at touchdown inside the cycle: LOC); small q 10.75 Hz line in 08; item 3 horizontal in 02/05/09.
- Run 17 log: motors unsaturated (max 0.27), measured torque valid, no telemetry fault: a closed-loop limit cycle from ~20 s.
- Linear model (existing margins_models.py, drawn factors per run): rate loop PM 36-79 deg on every draw; ATTITUDE loop (MC_ROLL_P /
  MC_PITCH_P 8 around the INDI rate loop) PM -16 to -0.6 deg at 1.6-1.8 Hz in exactly those 4 runs; 35 of the other 36 axis-runs OK.
  Boundary: unstable when e x tau_mult >= ~5 (e = controller G1 / plant G1, tau_mult = slow motor tau / 33 ms); PM < 30 deg above ~3.5.
  The G3 box reaches e 2 x tau 3 x asymmetry 3 = 18.
- PID reference on run 17's draw (one flight): also sustained p/q oscillation (2.75-3.25 Hz, 18-29 deg/s RMS), no LOC. So that row fails
  in both stacks on that draw; INDI's is ~10x larger and ends in LOC.
- Attitude P ~4.7 restores PM >= 30 deg at e 2, tau x3 (nominal attitude crossover 1.25 -> 0.7 Hz, PM 69 -> 78). With the slow-down
  corner (tau x3 and asymmetry x3 = down tau x9) even P 2 gives only 19 deg: no single gain covers the whole box.
Options:
  A. Keep the box. Set INDI-configuration attitude P to ~4.7 (stock params, values only, zero code diff), declare freeze-10, re-fly the
     G2/G4/G5 rows it invalidates (about 3-5 sessions). The down-tau x9 corner is then expected to fail and is reported as an explained,
     out-of-reach corner (G3 NOT PASSED there unless you narrow it).
  B. Narrow the box to what identification bounds (G6 flies G3 after identification): e.g. G1 error x[0.67, 1.5] and tau asymmetry
     applied inside x[0.5, 3] (down tau <= x3). Current gains then still fail at e 1.5 x tau 3 = 4.5 (PM < 30), so B alone is not enough.
  C. Attitude P scheduled from the identified motor tau (bandwidth rule, decision 4): a firmware design change (new law parameter,
     two keys, freeze-10). Covers the tau part, not the G1-error part.
  D. Keep gains and box, report G3 NOT PASSED with this boundary as the explanation, and move on to G6-G8.
Recommendation: A (and report the down-tau x9 corner as it falls). It is the smallest change that buys margin, and gives a
re-flyable freeze.
Meanwhile: no G3 flight or score of the oscillation rows. The key-2 item-3 fix (tooling, all options need it) finishes this session.
G4 waits Q20, G5 waits Q21, G7 waits the G4/G5 verdicts: blocked (WAIT_OWNER).
