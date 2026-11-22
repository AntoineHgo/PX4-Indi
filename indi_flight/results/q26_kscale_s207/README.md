# Q26 (S207): K scaled 1/tau_c vs fixed K 20, linear model check, no flight

**Method.** Same model and margin reading as `../g3_refly_s199/MARGINS_S200.md` (`bench/margins_models.py` L_indi / L_att_indi, `margins_est.margins`,
config `bench/g2_rate_model_s165.cfg`, 800 Hz, MC_ROLL/PITCH_P 8, measured torque path, Tb 1 s, plant glue g = 1/e, delay, n = 1 + tel frames).
Driver `q26_kscale.py` imports `cause_s199/margins_s200.py` unchanged (it only overrides K and tau_m/lead per case); no existing script modified, no new option.
Loops: rate = rate loop alone, rate+att = M3a break with attitude path closed, att = attitude loop. Plant tau = tau_slow = max(up, down) as in S200; the controller is the only thing varied.

Firmware (`src/lib/indi_rate_control`): lead c = min(lead_scale * K * tau_c, kMaxLeadGain = 2); setActuatorTimeConstant clamps tau_c to [0.001, 0.2] s; MC_INDI_K_R/P limits 1..100 (yaml).
quad5in values (`bench/params/quad5in_indi_defaults.params`, `g5_freeze_s157/params.params`): K 20, ACT_TC 0.033, LEAD 1, so **(K tau_c)_quad5in = 20 x 0.033 = 0.66 exactly**.
Rules: ACT_TC = ref 0.033 | a = tau_slow of the plant | b = 1.5 x tau_slow. Gains: fixed K 20 | scaled K = 0.66 / ACT_TC (so c = 0.66, cap never binds when scaled).
Box corners (realised G3 box, S200 sec 2b): plant tau x0.5 / x3 of 33 ms, delay 0 / 10 ms, e 0.8 / 1.2, tel frames 0 / 3 (16, pitch). The e 0.5 / 2 box of S200 sec 2a is also run (last table).
The tau x0.5 corner has ACT_TC 16.5 ms (a) -> K 40 (b: 24.8 ms, K 26.7); the tau x3 corner has 99 ms (a) -> K 6.7 (b: 148.5 ms, K 4.4).

**Reproduce** (from the repo root, ~1 min, no flight, no sim):
`python3 -I indi_flight/results/q26_kscale_s207/q26_kscale.py indi_flight/results/q26_kscale_s207`
The script first self-tests that ref/fixed reproduces S200 (245 drawn: rate 44 deg, rate+att 5.7 deg, att GM 3.1 dB; realised-box worst rate+att 5.7 deg) and that scaled = fixed at ACT_TC 0.033.
Outputs: `drawn.tsv` (3 draws x 6 cases, all loops: PM, GM, fc, delay margin), `corners_e0.8-1.2.tsv`, `corners_e0.5-2.0.tsv` (every corner x case), `worst.tsv`.

**Drawn plants** (PM deg / GM dB; DM ms in drawn.tsv). rate+att is what matters for 245/239 (S200), rate-only GM for 283.

| plant (tau_slow) | ACT_TC rule | gain | ACT_TC | K | K tau_c | rate PM/GM | rate+att PM/GM | att PM/GM |
|---|---|---|---|---|---|---|---|---|
| 245 pitch (99 ms) | ref | fixed = scaled | 0.033 | 20 | 0.66 | 44 / 24.9 | 6 / 24.9 | 24 / 3.1 |
| | a | fixed | 0.099 | 20 | 1.98 | 69 / 14.3 | 37 / 14.1 | 63 / 12.4 |
| | a | scaled | 0.099 | 6.7 | 0.66 | 77 / 26.3 | 25 / 26.4 | 37 / 11.2 |
| | b | fixed | 0.149 | 20 | 2.97 (cap 2) | 68 / 14.2 | 37 / 14.0 | 64 / 12.5 |
| | b | scaled | 0.149 | 4.4 | 0.66 | 89 / 26.4 | 33 / 26.5 | 42 / 14.7 |
| 239 roll (84 ms) | ref | fixed = scaled | 0.033 | 20 | 0.66 | 49 / 24.5 | 13 / 24.5 | 43 / 5.3 |
| | a | fixed | 0.084 | 20 | 1.68 | 71 / 15.7 | 39 / 15.6 | 64 / 12.9 |
| | a | scaled | 0.084 | 7.9 | 0.66 | 78 / 25.5 | 29 / 25.6 | 42 / 11.8 |
| | b | fixed | 0.126 | 20 | 2.52 (cap 2) | 72 / 14.2 | 45 / 14.0 | 67 / 14.0 |
| | b | scaled | 0.126 | 5.2 | 0.66 | 89 / 25.7 | 37 / 25.8 | 44 / 15.0 |
| 283 pitch (16.5 ms) | ref | fixed = scaled | 0.033 | 20 | 0.66 | 71 / 6.2 | 61 / 6.1 | 75 / 19.5 |
| | a | fixed | 0.0165 | 20 | 0.33 | 71 / 9.7 | 52 / 9.5 | 74 / 18.4 |
| | a | scaled | 0.0165 | 40 | 0.66 | 34 / 3.5 | 27 / 3.2 | 84 / 12.1 |
| | b | fixed | 0.0248 | 20 | 0.49 | 74 / 7.8 | 58 / 7.7 | 74 / 19.4 |
| | b | scaled | 0.0248 | 26.7 | 0.66 | 56 / 5.3 | 48 / 5.1 | 79 / 17.1 |

**Worst over the 16 realised-box corners** (e 0.8-1.2; worst PM deg / worst GM dB per loop; G2 thresholds PM >= 45, GM >= 6). Corner names: tauX_dDELAY_eE_frFRAMES.

| ACT_TC | gain | rate | rate+att | att | min PM / min GM | worst corner (rate+att PM) | cap binds |
|---|---|---|---|---|---|---|---|
| ref 0.033 | fixed = scaled | 42.8 / 4.2 | 5.7 / 4.0 | 24.1 / 3.1 | 5.7 / 3.1 | tau3 d10 e1.2 fr3 | 0 / 16 |
| a (tau_slow) | fixed | 53.3 / 7.0 | 35.9 / 6.8 | 60.4 / 12.3 | **35.9 / 6.8** | tau3 d10 e1.2 fr0 | 0 / 16 |
| a (tau_slow) | scaled | 18.0 / 1.7 | 13.8 / 1.4 | 37.3 / 7.2 | 13.8 / 1.4 | tau0.5 d10 e0.8 fr0 | 0 |
| b (1.5 tau_slow) | fixed | 52.8 / 5.5 | 36.2 / 5.3 | 61.2 / 12.3 | 36.2 / 5.3 | tau3 d10 e1.2 fr0 | 8 / 16 (all tau x3) |
| b (1.5 tau_slow) | scaled | 39.6 / 3.3 | 33.3 / 3.1 | 41.3 / 14.7 | 33.3 / 3.1 | tau3 d10 e1.2 fr3 | 0 |

No (rule, gain) pair meets PM 45 / GM 6 on every realised corner. Only a/fixed meets GM 6 (6.8) but not PM (35.9).
Same table on the e 0.5 / 2 box (outside the realised G3 box; worst rate+att PM / min over loops): ref -27 / -27 (both gains), a fixed 2 / -80 (att entry is a wrapped-phase read, as S200 noted; rate+att 2.2, rate GM +0.3), a scaled -49, b fixed -13, b scaled -35. Every rule has an unstable corner there (the tau x0.5, e 0.5, 10 ms corner); scaling makes it worse.

**Cap.** With fixed K 20 the lead cap (K tau_c > 2, i.e. ACT_TC > 0.1) binds only for rule b on the slow plants (245: 2.97, 239: 2.52; 8 of 16 corners, all tau x3), where c is held at 2; rule a stops just below it (245: 1.98). Scaled K never reaches the cap by construction (c = 0.66).
Not shown in the table: fixed-K rule a/b on the fast plant lowers c (0.33 / 0.49) and K tau_c < 0.66.

**Conclusion.**
1. Scaling K by 1/tau_c does not help: it is identical at ACT_TC 0.033, and with tau-matched ACT_TC it gains rate+att phase margin on none of the draws vs fixed K (245: 25 vs 37 deg, 239: 29 vs 39, 283: 27 vs 52) and loses GM on the fast side (283: 3.2 dB at K 40; corner worst GM 1.4 dB vs 6.8).
2. The benefit comes from matching ACT_TC to the slow plant (245 rate+att PM 6 -> 37 deg, att GM 3.1 -> 12.4 dB, 239 13 -> 39), with K left at 20: worst realised-corner PM 5.7 -> 35.9 deg, GM 3.1 -> 6.8 dB; the 1.5x round-up costs 1-2 dB of GM at the fast corner (5.3). The lead cap only matters for the round-up on slow plants and removes about 0.5-1 of c there.
3. Neither rule reaches PM 45 on all realised corners; the limiting corner is tau x3, delay 10 ms, 3 frames (a, fixed 35.9 deg) and, for scaled K, the fast plant (K 40 gives 1-2 dB GM).

**Limits of the model** (as in MARGINS_S200): linear, no position loop, saturation, motor tau up/down split (slow tau used), thrust sag, dropout; ACT_TC change evaluated only on the loop, not the weak-motor blend or yaw; on 283 the model had ~3 dB more GM than the log (|L| 0.63 at 10.75 Hz vs logged 0.92), so the fast-plant GM numbers (esp. the K 40 cases) are probably optimistic by that amount; delay lumped as command latency, gyro/dgyro cutoffs 40/20 Hz unverified. Mean-tau variant not run. The "perfect identification" tau is the plant's slow tau, which assumes the identification returns tau_slow rather than a mean; the ACT_TC clamp 0.2 s and K range 1..100 are respected (no case hits them). Not a flight claim.
