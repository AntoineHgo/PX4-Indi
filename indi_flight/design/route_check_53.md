# Route check 53 (sonnet, 2026-11-17, session 53)
Read: STATE, DECISIONS (headings, D-RATE-LEAD + addenda 1-2, D-G1.7), ANOMALIES (open rows A-1..A-6 only), JOURNAL tail,
GATES G2, stage3_items_note head, route_check_49. No source, nothing flown.

## 1. Shortest path?
Partly. On path: the lead is in, roll M3a passes G2 numbers (PM 59/GM 14 at 800 Hz, 2 seeds; STATE S52), the ACT_TC sweep
(S53) bounds the tolerance. G2 needs every loop, every rate, both paths, and 0 of 8 gates are passed after 53 sessions.
Measured so far: roll torque break, 800 Hz, model-only, one airframe tau. Not measured: pitch, yaw (with lead, F3), 400 Hz,
measured-rotor path, attitude/velocity/position breaks (no break notes exist, GATES G2 "Loops and break points").
Off-path / deferrable now: stage3_items_note items 1-3 (landed split, foreign-torque-publisher detection, thrust decay):
robustness items no gate in GATES.md G2 needs; item 3 the note itself doubts (diverges from stock). The $1.1 opus review of
that note (STATE NEXT (1)) is the same "opus review of a note" route_check_49 sec. 4 called polish. Also deferrable: the
hole reporter (G1 evidence limit 1) until a --gate batch is near; A-1..A-6 (all stage-1/5, untouched, fine).
On path and cheap: item 6 (defaults LEAD 1, ACT_TC 0.05): without it every default-parameter flight fails G2 (D-RATE-LEAD
addendum 2: ACT_TC 0.02 fails). That is a 2-line yaml change, blocked behind the unreviewed note.

## 2. Main difficulty is a consequence of
D-RATE-LEAD (S48) choice to keep the stock cascade (MC_ROLL_P 8) and fix it inside the INDI law (alternative (a) rejected).
The lead is feedback-only (addendum 1), so its benefit hinges on an identified tau_c; addendum 2 then makes ACT_TC an
identification-quality default with a one-sided tolerance [x1, x2]. Underneath: decisions 3/4 (derive every physical
parameter) written after stage 2 started (route_check_45/49).

## 3. Fresh start on stage 3
- Apply the model-derived defaults (LEAD 1, ACT_TC from the rotor step) and the unit-tested law first; fly G2 per axis on
  frozen code, all axes in one batch (roll, pitch, yaw, 800/400), instead of roll-first then widen.
- Treat landed/foreign-publisher/thrust-decay as a separate safety work package after the first full G2 table, reviewed once
  at the diff, not as a design note ahead of code.
- Write the attitude/velocity/position break notes in parallel on the host while the rate loops fly (never done).
- Run flights from host bash in the background (STATE lessons S53), agents only for drafting.

## 4. Previous recommendations (route_check_49 sec. 5)
1. Host-only falsifier of the lead at 400/800 Hz with delay: DONE (S49 sweep, S50 second key, K20 400 Hz PM 57/GM 10.5).
2. Implement MC_INDI_LEAD, one roll M3a, opus review of the DIFF: PARTLY. Implemented (S52) and flown; but opus reviewed the
   note (S51, $1.1, not the diff); the diff got a haiku key only.
3. Widen not deepen: pitch and yaw with lead at 800/400: NOT done (STATE "Later": yaw F3, pitch break, 400/250 Hz). Break
   notes for attitude/velocity/position: NOT done. Q2-Q4: done (S50).
Also from sec. 4 "polish": S51-S53 spent sessions on lead tolerance depth (sweep x0.5-x2) and a 168-line items note rather than
pitch/yaw.

## 5. Recommendations (ranked)
1. S54: skip the opus note review; apply defaults (LEAD 1, ACT_TC 0.05, item 6 only), rebuild, commit, then fly pitch and yaw M3a at 800 Hz with two seeds.
2. Then 400 Hz roll/pitch/yaw and the measured-rotor path (`--sim v2`) to complete one G2 table (GATES G2 Configurations).
3. Write the attitude/velocity/position break notes on the host now (free), second-keyed before first flight (GATES G2).
4. Park stage3_items_note items 1-3 as a post-G2 safety package; item 3 (thrust decay) dropped unless a flight shows a stall.
5. Add the per-run hole reporter (STATE S50 TODO) only when the frozen --gate batch is scheduled; do not build it earlier.
