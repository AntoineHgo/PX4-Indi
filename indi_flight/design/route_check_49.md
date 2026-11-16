# Route check 49 (sonnet, 2026-11-16, session 49)
Read: STATE, ANOMALIES (open rows), JOURNAL tail, DECISIONS D-RATE-LEAD / D-G1-DERIVE / D-G2Y-DERIVE, GATES G2 text,
route_check_45. No source, no logs, nothing flown. Numbers are those STATE records.

## 1. Still on the shortest path? Cheapest falsifier
Mostly yes, with a caveat. G2 (PM >= 45, GM >= 6 dB, every loop break, 400 and 800 Hz) is unreachable on roll by gains
at P_att 8 (best measured PM 42.9 at P3, STATE S48); D-RATE-LEAD is the one proposal whose model gives margin
(PM 56-61, GM 11-16). Caveats: (a) the model is 2-3.5 dB GM-optimistic and lacks the ~3-5 ms delay (T101); the lead's
margin is exactly what unmodelled delay erodes, so the 11-16 dB is the least trustworthy number on the table.
(b) One cell is addressed: measured margins today = roll torque break, 800 Hz only (summary_table.md). Pitch, yaw, 400 Hz,
PID, attitude/velocity/position/acceleration breaks: nothing measured, no break notes written.
Cheapest falsifier ($0, host, ~1 session slice): add 3-5 ms delay and ACT_TC 0.033 to `bench/margins_models.py`, recompute
the lead at 400 and 800 Hz, K 20-40, with the 1.4-2.3x noise factor. Falsified if PM < 50 or GM < 8 dB at 400 Hz.
Next cheapest: implement MC_INDI_LEAD, fly one roll M3a, same overturn rule as D-RATE-LEAD (> 10 deg PM off model).

## 2. Which earlier decision is the difficulty a consequence of?
- Keeping the stock cascade (MC_ROLL_P 8) and rejecting alternative (a) "slow attitude loop" for F-2 feel
  (DECISIONS D-RATE-LEAD), on top of a matched INDI law that ignores actuator lag (K_R 20 vs motor bandwidth ~30 rad/s).
- Underneath, per route_check_45: decisions 3/4 (derive defaults from the airframe) were left "to be written" while stage 2
  ran first; ACT_TC 0.02 vs plant 0.033 alone costs 5 deg / 9.5 dB (S48). The low PM is a design-time number that a
  60-line model calculation would have shown in S36, before any flight.

## 3. Fresh start on stages 2-3
1. One derive script first: G1 R/P/Y, G2_Y, ACT_TC (rotor step), delay; all from sdf, CA_*, one rotor step.
2. Model with attitude loop, delay, filters BEFORE the first margin flight; pick K_R, P_att and the lead from the model
   for PM >= 50 / GM >= 8 (slack for the known model error), then fly to confirm, not to discover.
3. Design the law (lead included) in stage 3, then measure margins once per axis on frozen code. Stage 2 ran on code that
   changed under it (A-21..A-26, five void sessions S40-S44).
4. Break notes for attitude/velocity/position written in parallel on the host (free), not after roll is done.

## 4. Pace
S36-S49 = 14 sessions (~$3 each, ~$35-40); gates passed 0 of 8 (G1 frozen, not passed, waiting on Q2-Q4).
Useful: estimator, models, M3a plumbing, derive_g1, pretest_gate, S48 explanation. Void: S40-S44 (5 sessions).
Polish no gate needs now: A-24 (46 Hz tone), A-26 (1-2 Hz phase), M3b store points, GM-gap hunting beyond a delay term,
a full opus review of a one-parameter note ($0.6), re-reading the same A-10/A-13 parked items. Q2-Q4 sit unanswered and
cost nothing to ask.

## 5. Recommendations (ranked)
1. Host-only falsifier of the lead (delay, ACT_TC 0.033, noise) at 400 and 800 Hz; go/no-go before any code.
2. If go: implement MC_INDI_LEAD with a unit test, fly roll M3a once, review the diff (not the note) with opus.
3. Then widen, not deepen: pitch and yaw at 800/400 with the lead, and write the attitude/velocity/position break notes; ask Q2-Q4.
