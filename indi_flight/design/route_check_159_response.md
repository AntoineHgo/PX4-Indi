# Orchestrator response to route check 159 (S159)

- Accepted: order after G5 keying is G2 freeze cells -> G4 -> G3 (G3 needs the most tooling). Rationale: G2/G4 are
  short and a firmware change they force re-flies G5 rows only, which is what D-FREEZE-6 already states.
- Corrected: the check's G3 estimate (12-15 flights) did not read GATES; G3 requires >= 300 runs after a ~20-run
  pre-test (GATES section 3). G3 is CPU-heavy, token-light if run as one unattended batch with g3_checks.py keyed.
- Not accepted: keying one seed per clean row. The keys were already written for all seeds (scripts take N dirs, the
  marginal cost of extra seeds is CPU only), and D-FREEZE-6 says each checker keyed before its verdict counts.
- Accepted: no further G5.5 / G5.10 / G5.8 3 m/s / G5.9a work until Q9/Q11/Q8 answers.
- Fwdef G5.1 cell: reported line already in STATE; it is a lesson-12 finding for G7 (firmware defaults vs validated
  configuration), added there rather than as an owner question.
