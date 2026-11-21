# Route check 173 (S173, 2026-11-21)

## 1. On the shortest path?
Yes for G4 until S171; no since. G2 (freeze) and G4 metric rows (18/18 plus 3/3) are done. S171-S172 spent two
sessions and two code decisions (D-JFF-SOURCE, D-JFF-OFFB) on A-56, one clause of one gate item, and both
fixes left the failure rate at 1/3. The FF hypothesis is dead; a third chase of the same kind is off path.

## 2. A-56 cause (hypothesis, UNVERIFIED)
Onset (93.5 s) precedes land entry (96.1 s), FF is 0, and the failing seed changes with the code (s2, then s3):
a marginal 2 Hz loop, excited by noise, not by a mode switch. Most likely consequence: the stage-5 outer-loop
INDI that feeds the measured acceleration (accel std 1.9 m/s^2 at harsh) into the position/accel increment,
together with D-GAP (S70) collective blend (tb 1.0 s, shared with the eRPM-loss path), which sets the
slow collective/accel correction time scale near 2 Hz. D-NOISE-PROF (harsh 27 m/s^2 line, about 19 RMS, above
ArduPilot class RMS 15/30 by judgement, no 5-inch measurement) is second: harsh may be
unrealistically severe, but the gate text fixes it, so it is a report caveat, not a reason to move it.
Re-open first: the outer-loop measured-acceleration path decision (accel filter and its use in the a_cmd
increment), then D-GAP blend. Do NOT touch the detector: it flags a real 2 Hz roll/pitch rate oscillation.
Probe (2 flights, harsh_s3 at aa4fd2654a, the known fail, same seed so deterministic where possible):
 (a) replace the outer loop measured acceleration by the truth acceleration (truth hook inst 1 exists), flight 1;
 (b) same flight with collective blend off (tb 0) only if (a) still oscillates.
(a) clean -> the measured-accel noise path is the cause (fix = filter/gain, one decision). (a) still oscillates
and (b) clean -> D-GAP. Both oscillate -> inner/attitude loop margin at 2 Hz, go to G2 cells, not a new chase.

## 3. Fresh start would
Write the G4 harsh hover pretest and the whole-flight spectral detector first, before choosing outer-loop gains, and take the measured accel through one declared filter with a noise budget from the profile. It would not
have taken the stock auto-mode jerk as a rate FF at all (S171-S172 cost two sessions for a path nobody needed).

## 4. Moved since RC168
G4: metric script keyed, truth hook verified, harsh/typical/quiet hover batch flown: R20/R4/C20/clip PASS 18/18;
chatter clause FAIL 9/9 incl. quiet (A-54, Q14 owner question, clause non-discriminating); item 2 FAIL 1/3 harsh (A-56).
G3: checker keyed (key1+2), D-G3-SPAN, no campaign run. G5, G6-G8: unchanged. G2 cells unchanged.

## 5. Drop or simplify
- Drop: any further FF / jerk-source work (D-JFF-OFFB stays, one-line, keyed); the offboard-entry omega_ff step
  MINOR (defer to G7); G5.3/G5.4 re-fly at aa4fd2654a only if G3 touches those modes (fold into G3 batch).
- Drop: G4 typical/quiet re-flights (pass >= 10x margin).
- Simplify: ask owner Q14 as a single A/B (waive chatter clause as non-discriminating, state R20/C20 as
  evidence); do not build more spectral analysers.
- Build the G3 campaign (300 runs) as one unattended chain with one status file, serial, no per-run analysis.

## 6. Recommendation
Yes, with one carve-out. Write the G4 verdict now: metric rows PASS, chatter clause per Q14, item 2 an OPEN FAIL
(1/3 harsh, A-56, bound: no LOC, tilt < 11 deg). Run the 2-flight probe above once (about one session at most),
then start the G3 pre-test (~20) regardless of its result; an A-56 fix, if probe (a) names it, lands as one
decision with a harsh re-fly inside the G3 batch. Never weaken the detector to close it.
