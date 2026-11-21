# G2 outer loops at freeze-7 (S177 cells), scores

Command (repo root; the README's keyed scripts run on copies with the results path g2_outer_freeze_s163 replaced by g2_outer_freeze7_s177):
`sed 's/g2_outer_freeze_s163/g2_outer_freeze7_s177/' indi_flight/bench/g2_freeze_table_s163.py > $S/tab7.py; python3 $S/tab7.py` (primary table)
`sed 's/g2_outer_freeze_s163/g2_outer_freeze7_s177/' indi_flight/bench/g2_key2_outer_s164.py > $S/key2_7.py; python3 $S/key2_7.py` (second key, wrote key2.md here; HERE hard-set to the repo bench dir)
Hole check: `grep OVERALL *_holes.txt`. Limits: PM >= 45 deg, GM >= 6 dB (phase-crossover GM and key2 plateau GM both shown; GM n/a = no -180 crossing in the 0.2-8 Hz band),
DM >= 2 control periods + latency (2.5/5 ms + telemetry; all measured DM are 190-280 ms so never binding). PM/GM/DM from the primary margins.json.
Model prediction (g2_outer_model_s177.md): xy PM 46.0 / 46.3 deg (800/400), GM 7.9 / 7.8 dB, f_c 0.62 Hz. Measured xy: PM 38.4-47.4 deg, GM 11.3-12.9 dB, f_c 0.52-0.59 Hz.

| cell | GM dB | plateau GM dB (key2) | PM deg | DM | limit | verdict | notes |
|---|---|---|---|---|---|---|---|
| pt0_ax1_r400_s1 | 11.3 | 11.5 | 40.0 | 215 ms | PM>=45, GM>=6 | FAIL (PM 40.0<45) | holes FAIL (sim,controller); coh>=0.8 bins 16/17; key2 agree |
| pt0_ax1_r400_s2 | 11.7 | 11.9 | 41.7 | 221 ms | PM>=45, GM>=6 | FAIL (PM 41.7<45) | holes PASS; coh>=0.8 bins 15/17; key2 agree |
| pt0_ax1_r800_s1 | 12.0 | 12.2 | 39.5 | 205 ms | PM>=45, GM>=6 | FAIL (PM 39.5<45) | holes FAIL (controller); coh>=0.8 bins 17/17; key2 agree |
| pt0_ax1_r800_s2 | 12.1 | -10.9 | 42.0 | 217 ms | PM>=45, GM>=6 | FAIL (PM 42.0<45) | holes PASS; coh>=0.8 bins 16/17; key2 agree |
| pt0_ax2_r400_s1 | 11.4 | 11.9 | 38.4 | 189 ms | PM>=45, GM>=6 | FAIL (PM 38.4<45) | holes PASS; coh>=0.8 bins 17/17; key2 agree |
| pt0_ax2_r400_s2 | 11.6 | 11.9 | 46.0 | 235 ms | PM>=45, GM>=6 | PASS | holes PASS; coh>=0.8 bins 16/17; key2 agree |
| pt0_ax2_r800_s1 | 12.4 | 12.5 | 40.0 | 208 ms | PM>=45, GM>=6 | FAIL (PM 40.0<45) | holes FAIL (sim,controller); coh>=0.8 bins 16/17; key2 agree |
| pt0_ax2_r800_s2 | 11.6 | 11.9 | 43.7 | 208 ms | PM>=45, GM>=6 | FAIL (PM 43.7<45) | holes FAIL (sim,controller); coh>=0.8 bins 15/17; key2 agree |
| pt0_ax3_r400_s1 | n/a | n/a | 71.1 | 282 ms | PM>=45, GM>=6 | PASS on margins only (not clean) | holes PASS; coh>=0.8 bins 16/16; key2 BLOCKED |
| pt0_ax3_r400_s2 | n/a | n/a | 68.5 | 257 ms | PM>=45, GM>=6 | PASS on margins only (not clean) | holes FAIL (controller); coh>=0.8 bins 15/16; key2 agree |
| pt0_ax3_r800_s1 | n/a | n/a | 68.3 | 281 ms | PM>=45, GM>=6 | PASS | holes PASS; coh>=0.8 bins 15/16; key2 agree |
| pt0_ax3_r800_s2 | n/a | 28.7 | 64.2 | 270 ms | PM>=45, GM>=6 | PASS on margins only (not clean) | holes FAIL (controller); coh>=0.8 bins 14/16; key2 BLOCKED |
| pt1_ax1_r400_s1 | 12.4 | 12.3 | 47.2 | 248 ms | PM>=45, GM>=6 | PASS on margins only (not clean) | holes FAIL (sim,controller); coh>=0.8 bins 15/17; key2 agree |
| pt1_ax1_r400_s2 | 12.2 | 12.3 | 42.6 | 226 ms | PM>=45, GM>=6 | FAIL (PM 42.6<45) | holes PASS; coh>=0.8 bins 15/17; key2 agree |
| pt1_ax1_r800_s1 | 12.6 | 12.5 | 43.0 | 228 ms | PM>=45, GM>=6 | FAIL (PM 43.0<45) | holes PASS; coh>=0.8 bins 16/17; key2 agree |
| pt1_ax1_r800_s2 | 12.6 | 12.6 | 47.4 | 237 ms | PM>=45, GM>=6 | PASS | holes PASS; coh>=0.8 bins 16/17; key2 agree |
| pt1_ax2_r400_s1 | 12.2 | 12.1 | 44.7 | 234 ms | PM>=45, GM>=6 | FAIL (PM 44.7<45) | holes FAIL (controller); coh>=0.8 bins 15/17; key2 agree |
| pt1_ax2_r400_s2 | 12.3 | 12.2 | 43.8 | 223 ms | PM>=45, GM>=6 | FAIL (PM 43.8<45) | holes PASS; coh>=0.8 bins 15/17; key2 agree |
| pt1_ax2_r800_s1 | 12.9 | 12.5 | 44.8 | 236 ms | PM>=45, GM>=6 | FAIL (PM 44.8<45) | holes FAIL (sim,controller); coh>=0.8 bins 15/17; key2 agree |
| pt1_ax2_r800_s2 | 12.5 | 12.6 | 44.8 | 233 ms | PM>=45, GM>=6 | FAIL (PM 44.8<45) | holes FAIL (sim,controller,logger); coh>=0.8 bins 15/17; key2 agree |
| pt1_ax3_r400_s1 | n/a | n/a | 64.2 | 262 ms | PM>=45, GM>=6 | PASS | holes PASS; coh>=0.8 bins 15/16; key2 agree |
| pt1_ax3_r400_s2 | n/a | n/a | 61.5 | 240 ms | PM>=45, GM>=6 | PASS on margins only (not clean) | holes FAIL (controller); coh>=0.8 bins 16/16; key2 BLOCKED |
| pt1_ax3_r800_s1 | n/a | n/a | n/a | n/a ms | PM>=45, GM>=6 | FAIL (no valid margin (coherence)) | holes FAIL (sim,controller); coh>=0.8 bins 0/16; key2 agree |
| pt1_ax3_r800_s2 | n/a | n/a | 63.0 | 274 ms | PM>=45, GM>=6 | PASS on margins only (not clean) | holes FAIL (controller); coh>=0.8 bins 13/16; key2 agree |

**Total: 10/24 meet the margin limits (4/24 also have holes PASS and key2 not BLOCKED); 14/24 FAIL (xy cells fail PM; pt1_ax3_r800_s1 has no coherent bins, invalid, counted FAIL).**
Notes: key2 plateau value pt0_ax1_r800_s2 = -10.86 means |L|>1 near -180 deg (Q13 A gain-reduction margin 20log|L| = 10.9 dB, >= 6); the s164 key2 script predates Q13 A and prints it as negative. 'key2 BLOCKED' = own vs primary disagree > 3 deg / 1 dB (gates block the result). Hole FAIL = sim or controller missing-sample limits exceeded, see *_holes.txt; the README treats hole FAIL as non-invalidating only for topics outside the loop under test.
