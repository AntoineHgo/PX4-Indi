# Questions to the owner

No open question (S50). Q1-Q4 closed, archived in JOURNAL.md.

N1 closed S61 (moved to JOURNAL.md; open items C2, C3 carried in STATE.md).

N2 closed S69 (summary in JOURNAL.md).

Q5 closed S70 (no owner objection to addendum 6; summary in JOURNAL.md).

Q6 closed S120 (owner answer B, conditions (i)-(v) in DECISIONS.md D-IDENT; full text in JOURNAL.md).

Owner directive 2026-11-20 (F-7/F-8/F-9) closed S134: acted on (DECISIONS D-F7-GROUND, GATES 5b, STATE
next actions); text in JOURNAL.md.

## Q7 (S139, 2026-11-20): G5.7 validity rule, change after first test. Not blocking.
Context: G5.7 exact test (GATES 5b, S139) flown x3 (results/g5_g57_s139). All 10 switches happen as commanded,
thrust step <= 3.1 % of hover (limit 20 %), no LOC. Runs are INVALID: the rule "truth speed >= 1.5 m/s at >= 8 of 10
edges" cannot be met, because HOLD brakes by design (speed at H->P edges 0.0-0.1 m/s; A/S coast to ~1 m/s in 2 s).
Under any validity rule that admits the runs, tilt error over [edge+0.3, edge+1.0] s is 4.4-5.25 deg at the two H->P
edges (limit 5 deg): FAIL in 2 of 3 seeds. Being compared with the same measure on G5.2 posctl stick steps from rest
(no switch) to tell switch transient from normal attitude lag to a stick acceleration.
Options: (A, recommended) validity = speed >= 1.5 m/s at the 4 edges that leave posctl; all 10 edges stay gated with
unchanged limits (stricter than dropping edges). (B) re-design the sequence (shorter hold dwell) and re-fly.
(C) keep as written: G5.7 cannot produce a valid run.
Meanwhile: runs re-scored under A, marked "pending Q7"; no G5.7 verdict is claimed.
