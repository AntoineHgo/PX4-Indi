# Route check 163 (written for S164)

Read: STATE.md, DECISIONS (headers, tail D-FREEZE-6..D-T10-RESET), ANOMALIES (open-row list only), JOURNAL tail 5,
GATES G2 "Freeze status" + G2 pass/x-check/key text (lines 108-134), route_check_149.md. Not read: result READMEs.

## 1. Still on the shortest path?
Yes for G2, with one caveat. S160-S163 flew the whole G2 set serially at the freeze (rate, attitude, outer: 52+ cells)
and keyed rate and attitude. What is left for G2 is offline analysis on data already in hand, no new flying except the
267 Hz rows. The caveat: G5.11 xy (Q12), G5.5, G5.9a and the G3/G4 items are owner-answer or gate-text problems, not
code; more G5 work now does not shorten the path. G4 and G3 are not started at the freeze, so they are the long pole;
G2 should be closed in at most 2 sessions, then G4.

## 2. Decision behind the difficulty
- Open G2 items: the gate's own text (cross-check, second key, phase-plateau rule, 267 Hz reported), plus D-FREEZE-6
  "keyed before its verdict counts". Not a design decision; a tooling gap: no outer-loop model in margins_models.py
  and no outer key2 (T78 unmodelled list).
- Residual G5 failures: D-outer-arch base A (stock PositionControl a_c; G5.5, G5.10), Q8/Q9/Q12 gate-text limits.
- S161 yaw spike: T10 reset branch design (fixed, D-T10-RESET).

## 3. Fresh start on this stage
Same freeze. Differences: build the outer-loop linear model and key2 before flying the 24 outer cells (as GATES line 152
already required), so cells are keyed the day they are flown; keep one flying host rule (no docker in parallel) from
S160, not after 3 re-flown cells; and write the G5 limits the owner approves (Q8/Q9/Q12) before the freeze re-fly.

## 5. Gate items moved since RC159 (JOURNAL S161-S163)
- G5.11: yaw 0/3 -> 2/3 PASS (T10 fix d1b65d0f09), xy 0/3 FAIL (Q12), row FAIL as written, KEYED. G5.8/G5.9 unchanged.
- G2: attitude 12/12 PASS keyed (worst PM 53.4 deg, GM 19.2 dB, DM 106 ms); rate set complete and keyed (16 model-only +
  measured + fwdef roll 800); outer 24/24 meet thresholds, UNKEYED. G1, G3, G4, G6-G8 unchanged. Not closed: G2.

## 6. Drop or simplify (no threshold weakened)
Required by the G2 gate text, keep: outer margin key2 (blocks the result, >1 dB/3 deg rule); phase-plateau rule (pass
uses min of GM and plateau GM; one offline pass over existing CSVs, do it for all cells, z included, not a separate
z check); linear-model x-check or an ANOMALIES explanation, for outer cells too.
Scope down, same thresholds:
1. Outer model: a minimal analytic loop (z, then x/y by symmetry) is enough; x-check bound is 10 deg/3 dB or an
   explained difference. If it disagrees, explain in ANOMALIES, do not tune the model to fit.
2. Rate-at-freeze-params and yaw model x-check: reuse margins_models.py with freeze params; run as one script over
   all cells in one session, not per-axis sessions.
3. 267 Hz: gate says REPORTED, not pass. Cheapest honest option: one roll rate/attitude cell and one outer cell at
   267 Hz, 2 seeds, serial, tagged "reported"; the remaining 267 rows stay "analytic only" and are named as such. Whether
   that satisfies "reported" is the owner's call (ask, do not assume). Do not hold G4 for it.
4. Do not key2 by a sonnet brief with raw ULog if the existing second_key_margins_s37-style code can take the CSVs the
   gate names ("same CSV windows"); the raw-ULog route is stronger but costs more, pick it only if the CSV route is
   not independent of pinj_csv.py.
5. STATE: cut S160/S161 prose in item 0e (history is in JOURNAL) and the STOP/deferred lists already dispositioned;
   G5 items 0b-0d, 4, 4a to one line per row; keep the G2 todo list.

## Next 2 sessions
- S164: outer key2 + plateau pass over all freeze cells + outer/yaw/rate model x-check scripts; write ANOMALIES
  rows for any gap > 10 deg / 3 dB.
- S165: 267 Hz reported cells (owner scope), update G2 Freeze status, then open G4 (profiles exist, D-NOISE-PROF) per
  RC159 order. No G5 chase.
