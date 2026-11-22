# G3 campaign speed factor: speed 4 against the speed-1 same-seed spread (owner, 2026-11-22)

Question: can the 300-run campaign fly at sim speed factor 4 (about 45 s per run, 3.75 h) instead of 1 (108 s per run,
9 h) without changing what G3 measures? Bears on A-4 (INDI sensitivity to the speed factor) for the G3 set-up only.

## Flights (same draws, binary d220e193..., FREEZE-10 params, seed 173 n 300, idx 0-19)
- s1a: the speed-1 pre-test (`../../g3_pretest_q24_s197/` for the 14 changed draws, `../../freeze10_s193/g3_pretest/`
  for 00 06 07 14 15 19).
- s1b: the same 20 draws flown again at speed 1 by the chain (`../../g3_speed1_repeat_f10/`): the same-seed spread.
- s4: the same 20 draws at speed 4 by the chain (`../../g3_speed4_check_f10/`, `g3_run.py --speed 4`).
- Draws checked identical (`g3_draw.json` differs only in output paths and the `--speed 4` argument). 17 draws are
  offboard trajectories whose setpoints are a sim-time schedule inside PX4 (896 rows in sched.txt at both speeds);
  04, 10, 16 are stick flights (`stick_zsine_o6`), whose MANUAL_CONTROL is sent by the runner on a sim-time grid, so
  any runner latency is 4x longer in sim time at speed 4.

## Result (`cmp3.py`, output `cmp3_output.txt`)
|diff| as a fraction of the item threshold, median / max over the 20 draws:

| metric | s1a vs s1b (same-seed spread) | s4 vs s1a | s4 vs s1b |
|---|---|---|---|
| tilt max | 0.00 / 0.02 | 0.00 / 0.04 | 0.00 / 0.04 |
| item 3 horizontal RMS | 0.04 / 0.16 | 0.04 / 0.15 | 0.03 / 0.11 |
| item 3 altitude mean | 0.20 / 0.98 | 0.21 / 1.37 | 0.16 / 0.46 |
| roll mean | 0.03 / 0.26 | 0.06 / 0.22 | 0.06 / 0.13 |
| pitch mean | 0.04 / 0.19 | 0.05 / 0.16 | 0.06 / 0.28 |

Verdicts: s1a vs s1b 0 flips (17/20 both keys each). s4: key 1 15/20, key 2 16/20; flips on 2 draws, both borderline
at speed 1 too:
- 17 (both keys), item 3 altitude mean: s1a -0.003, s1b +0.095, s4 +0.134 m (limit 0.10). The 3 s window altitude mean
  moves up to 98 % of its limit between two speed-1 flights of one draw; s4 sits inside that spread.
- 09 (key 1 only), item 2: a 2.0 Hz p-axis line in 3 windows (the sustained rule needs 3); s1a had 0 flagged p windows,
  s1b 2. Key 2 does not flag it at either speed. 03 also gains a 2.25 Hz p line at s4 beside its known 2.0 Hz q line
  (03 fails item 2 at every speed; shared with PID, Q24 B).
- The 3 failing draws (02, 03, 08) fail at all three flights, with the same items; no speed-1 failure passes at speed 4.

## Decision (owner's session, 2026-11-22)
Fly the campaign at speed 4. Metric differences s4 vs s1 are within the measured speed-1 same-seed spread (medians
equal, maxima of the same order); the two verdict flips are draws whose speed-1 flights are themselves within the
spread of the threshold (G1.6 (d): such a verdict does not separate). Residual risk: item 2 (no quota) at speed 4 shows
two extra low-frequency p-axis lines near the detector's 3-window edge. Rule written in the campaign README: every
item 1-2 failure, and every item 3-6 miss within the same-seed spread of its threshold, is re-flown at speed 1 on the
same index before it is classified, and both flights are reported.
Not shown: speed equality for factors absent from draws 0-19 (corners C1-C6, acro, weak motor + saturation); the
speed-1 re-fly rule covers their failures.
