# Questions to the owner

No open question (S50). Q1-Q4 closed, archived in JOURNAL.md.

N1 closed S61 (moved to JOURNAL.md; open items C2, C3 carried in STATE.md).

N2 closed S69 (summary in JOURNAL.md).

Q5 closed S70 (no owner objection to addendum 6; summary in JOURNAL.md).

## Q6 (S119, 2026-11-18) Identification concept: how does INDI fly before identification? ANSWERED (B)
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
**Owner answer (2026-11-18): B.** INDI flies its own identification manoeuvre in the conservative ident
configuration; no PID dependency. Concern to close: INDI flying the manoeuvre must not bias the result. Conditions:
- (i) Start independence (acceptance test): in SITL, ident flights started from G1 x0.5, x1 and x2 must give the same
  estimate (spread within the 10 % convergence tolerance) and each within 10 % of the true quad5in values. An estimate
  that follows its starting value means the closed loop leaks into the fit: B fails.
- (ii) Excitation strength: INDI rejects the injected signal inside its bandwidth. Choose the multisine band against
  the halved-gain loop bandwidth, and report per axis the instrument strength (correlation of the instrument with
  du_meas, or the first-stage F statistic) and the confidence interval of each estimate. A weak instrument is a
  failed identification, not a value.
- (iii) Filter alignment: the regressor (du_meas) and the regressand (derived acceleration) pass through the same
  filter and delay; a self-test with a deliberate mismatch must fail.
- (iv) Identifiability: the excitation spans four independent directions (roll, pitch, yaw, thrust) whatever the
  starting G1; check the conditioning of the regression and report it.
- (v) Cross-check, once in SITL: the same estimator on a PID-flown manoeuvre gives the same values within tolerance.
SITL validates the estimator only; unmodelled effects (prop wash, frame flex, ESC non-linearity) stay in G4/G6
scope.
