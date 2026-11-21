# Route check 154 (written for S154)

Read: STATE.md, ANOMALIES.md (no open G5 entry), QUESTIONS Q8/Q9, DECISIONS D-PREFREEZE-R1 (D-GAP-G510 via
JOURNAL), route_check_149.md, JOURNAL tail 8, GATES headers. Not read: code, results, full G5 text, other decisions.

## 1. Still on the shortest path?
Yes for S150-S153: G5.10 went from FAIL to probe PASS (alt 1.74-1.76 m) in two sessions, and review 1/3 found a real
BLOCKING defect (ALTCTL ground arm) that a freeze would have baked in. Risk now: the pre-freeze review is turning into
a fix-and-reprobe loop (S152-S153, two sessions, one review). Every remaining item that blocks the freeze is
either a review or an owner question, none is a new design problem. Go to the freeze after review 2/3 is dispositioned.

## 2. Which decision is the difficulty a consequence of?
- Review findings F1-F4: D-F7-GROUND (INDI from arming; ground handled by the model) plus D-GAP (blend state kept
  across edges) and D-outer-arch base A (INDI stage behind stock chain, many entry/exit edges to reset). Ground arm,
  re-entry and hold-exit are all edges of that structure.
- Open failing rows (G5.5 o1-o4/o7, G5.9a, G5.8 3 m/s, G5.10 tilt/AGG): base A (stock a_c) and gate text vs stock
  commander (Q8, Q9). Not code problems.

## 3. Fresh start on this stage
Same base A. Differences: (a) one edge-case table (arm, disarm, mode entry/exit, hold, stale) written and tested
before the first gate probe, so review finds nothing structural; (b) gate rows with physics-achievable limits agreed
with the owner first (G5.10 tilt 20 deg, 3 m/s excursion, G5.9a reference); (c) sim set-up check (GNSS delay,
atomic injection) first; (d) one review of the whole diff, not three, since interfaces were small.

## 5. Gate items moved since RC149 (S149)
- G5.10: FAIL 2.67-2.74 m -> alt loss 1.74-1.76 m and back 1.9-2.0 s PASS 3/3 (probe, TB 0.3, kMaxBlend 0.5);
  tilt 45.3 deg and AGG/SAT definition still wait on Q9. Cause was D-GAP (blend too slow), fixed in firmware.
- G5.4: PASS at TB 0.3 (s1, edge 4.0/4.4 %). G5.2/G5.4 ground-arm path: defect fixed, probe PASS (edge 7.2/7.1 %).
- G5.7: holds after F3/F4 fix (3.71 deg, 2.6 %, s1). G2: outer z cells at TB 0.3 measured (PM 62.7/67.3 deg), xy
  PM 51.4/65.2 deg, GM 16.8 dB. G7: review item 1/3 done. Unchanged: G5.5, G5.6, G5.8 3 m/s, G5.9a, G5.11, G3, G4,
  G6, G8. Q8/Q9 still unanswered (both marked NOT blocking).

## 4. Next 2-3 sessions (ordered)
1. S154 (G7 pre-freeze item 2/3): review of the stage-3 inner-loop safety diff, opus, one pass. Pass condition:
   no BLOCKING; MAJORs get a one-line disposition in a D-PREFREEZE-R2 entry, fixes only if they can fail a
   G2/G3/G5 limit. If BLOCKING, fix, key2, no re-review of the whole diff (check the fix only).
2. S155 (G7 item 3/3 + G5 freeze prep): module_parity.md review, shrunk (see 6.2), and in the same session the
   freeze check list: tree clean, parameters pinned, G2 firmware-default cell added (STATE 4b). Put Q8/Q9 to the owner
   as one message with recommended options A, including "freeze proceeds on the recommended options".
3. S156 onward (G5 gate evidence, G2, G3): stage-6 freeze, then re-fly G5.1-G5.11 with 3 seeds, serial, keyed
   checkers, one batch. Gate criteria first: a row failing on stock-stack limits is reported FAIL with the number.

## 6. Drop or simplify
1. Q8/Q9 do not block the freeze. Both are definition questions about rows whose result at the recommended option is
   known (G5.9a FAIL stock latency, G5.10 tilt = MPC_TILTMAX_AIR). The freeze text records "answer pending, option A
   assumed"; if the owner answers B, only the verdict changes, not the firmware. Do not wait on them.
2. Merge review 3/3 into a small check: module_parity.md is an open-per-item list from an external review; compare it
   against the code in a checklist (item, present/absent, evidence line), sonnet or haiku plus one opus key on the
   items marked absent. Skip a full opus review. Review 2/3 stays opus: it is the inner-loop safety diff.
3. Do not fix MINORs (K2, K5, F7, F8) before the freeze; they are bounded and have reopen triggers. K5 goes with
   the stage-7 harness.
4. No more G5 probes on rows already PASS as probes: the freeze re-fly is the evidence. No G5.5 chase (STOP list).
5. After 2/3 and 3/3, no 4th review; any firmware change after them gets key2 only, then freeze.

## Summary
Route is sound; the freeze is 2 sessions away. Open question to the owner is bundled, not blocking.
