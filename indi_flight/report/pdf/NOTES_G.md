# Notes G: chapters 6 and 7

## Discrepancies settled at the raw data
1. G3 item 2 "79 of 297" vs "79 failing runs, item 2 on 73": results/g3_campaign_f10/SCORES.tsv (297 ok rows) gives item 2 failing on 73 runs in key 1, 45 in key 2, 39 in both, 79 in the union. Key 1 also has 6 runs failing item 3 only, so key 1 has 79 failing runs in total (73 item 2 + 6 item 3 only; 15 item 3 misses overall). So "item 2 fails on 79 of 297" is right as "on at least one key". Ch06 says this.
2. G2 z outer cells "4 of 8" vs "7/8": freeze10_s193/G2_SCORES.md primary GM column is n/a in 7 of 8 ax3 cells (only pt1_ax3_r800_s2 has 22.4 dB). 7 of 8 is right. "4 of 8" survives in report/02_outer_loop_design.md line 314 (source md, not edited); ch05 already says 7 of 8.

## Source disagreements and unverified values
- G3 gain-error box: GATES.md amends it to x0.8-1.2 (Q22), but the recorded campaign draws (run_*/g3_draw.json g1_ctrl_mult) range 0.615-1.694, and the GATES factor table and 03_validation.md still show x0.5-2. Not resolved; stated in ch06 (G3 "Gain range as drawn").
- "mass 1.3" in draw 264: read as mass 30 % above nominal (GATES corner C3 "mass +30 %"); 01_inner_loop_design.md flags the unit as not stated.
- G1.1 "logger completeness -0.014 %": sign not explained in the source; ch06 says "within the limit".
- Number of unverified claims (47, 20 checked) from GATES G8 verdict; not recounted.
- J_r = 5e-6 unit not given in the source (written "SI units"). G1_Y IV fit 163-166 unit assumed rad/s^2 like the default 205.
- G7 test counts: 239 (S252 head) and 244 (after arming check) both from GATES.md; "seven weak or missing rows" = 4 MISSING + 3 WEAK.
- 70-78 Hz motor command lines (anomalies) summarised from 04_limits.md headlines only.
- Cause of the lower freeze-10 roll PM (46.9 vs ~69 deg): not established in sources.
- Fallback limits: only what 01_inner_loop_design.md and 04_limits.md state; no flown test of loss in flight beyond what they say.
- Figures: step_attitude, g3_campaign, g4_noise_effort, g5_modes, limits_failures used; g2_margins/g2_bode already in ch03/ch05.
