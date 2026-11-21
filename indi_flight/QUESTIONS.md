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

## Q16 (S175, 2026-11-21): G2 verdict with 3/15 rate model x-check groups unexplained. BLOCKING for G2.
Context: every G2 cell passes at the freeze, keyed: rate/att/outer 67/67 incl. the Q13 A plateau rule (key2 S175,
results/g2_plateau_s164_key2.md, max diff 0.22 dB); worst measured GM 10.7 dB (plateau, model-only roll/pitch 400),
PM 54.3 deg. G2 also says "measured and model PM within 10 deg and GM within 3 dB, or the difference explained in
ANOMALIES.md before the result is used". Rate x-check (A-51, results/g2_freeze_s160/xcheck_rate.md): 12/15 groups agree;
roll400 GM 14.2 vs model 17.9, yaw400 GM 15.3 vs 21.5, roll800 fwdef PM 54.3 vs 65.9. The closing test (S175,
xcheck_rate_a51.md) added the measured cmd->eRPM latency (2.1/4.1 ms): agreement fell to 5/15, hypothesis rejected.
The residuals are unexplained (likely yaw model structure and filter roll-off; not chased). In every group BOTH the
measured and the model margins pass (model min 7.9 dB/48 deg with latency), so no pass depends on which one is right.
Outer x-check: A-50, model conservative, explained.
Options: A [recommended] G2 PASSED on the keyed measured margins; the 3 unexplained groups are reported as an evidence
limit (model fidelity, A-51 open). The rule "a margin that passes only because it disagrees with the model is not a
pass" is met (the model passes too). B: one more session of model structure work (yaw reaction-torque path,
filter roll-off) before the verdict. C: G2 NOT PASSED on the x-check clause.
Meanwhile: no G2 work; G4/G5/G3 work continues.
