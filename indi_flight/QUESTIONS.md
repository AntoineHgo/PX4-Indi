# Questions to the owner

No open question (S50). Q1-Q4 closed, archived in JOURNAL.md.

N1 closed S61 (moved to JOURNAL.md; open items C2, C3 carried in STATE.md).

N2 closed S69 (summary in JOURNAL.md).

Q5 closed S70 (no owner objection to addendum 6; summary in JOURNAL.md).

## Q6 (S119, 2026-11-18) Identification concept: how does INDI fly before identification? OPEN
Context: stage 4 (decision 3). Full note: `design/ident_concept.md`. G1, G2_Y, ACT_TC, telemetry latency, W_MAX and
the outer-loop thrust model are identified in one ~60 s hover manoeuvre: small injected multisine per axis,
instrumental-variable regression of gyro/accel-derived acceleration on the measured rotor-speed increment (eRPM), with
intercept, saturation excluded. That estimator is controller-agnostic. The open choice is what flies the manoeuvre:
- B (recommended): INDI itself, in a conservative ident configuration (rate and outer gains halved, so a G1 wrong by
  x0.5 still has >= 6 dB / 45 deg, to be proven by G2 cells); full gains unlock when an ident-status parameter is set
  and the values pass plausibility checks. No PID needed (fits F-1 and "any quadcopter").
- A: the user flies the manoeuvre on the default PID stack, then selects INDI (needs a PID tune first).
- C: INDI refuses to arm until an offline log identification (same estimator on a PID log) wrote the parameters.
- D: online adaptive estimation (kept as outlook only).
Meanwhile: I build and key the estimator and its synthetic closed-loop self-tests (needed by every option), then G2
cells at G1 x0.5/x2 with halved gains. Not blocked.
Answer:
