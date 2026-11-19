# INDI defaults for quad5in (S127 draft)

Policy: D-IDENT (DECISIONS.md:626-641). Params file: bench/params/quad5in_indi_defaults.params.

## 1. Table

| parameter | firmware default | proposed quad5in | class | source | flag |
|---|---|---|---|---|---|
| MC_INDI_EN | 0 | 1 | switch | yaml; bench 1 (13 uses) |  |
| MC_INDI_W_MAX | 0 | 2700 | physical, identified | airframe 4040_gz_quad5in SIM_GZ_EC_MAX; bench 2700 (3) or 0 (3) | Mismatch: 0 disables measured torque (O-5) |
| MC_INDI_G1_R | 320 | 1757 | physical, identified | bench/params/quad5in_indi_g1.params:5; fit_s124 0.8 % | firmware 5.5x low |
| MC_INDI_G1_P | 210 | 1640 | physical, identified | same :6; fit_s124 0.8 % | firmware 7.8x low |
| MC_INDI_G1_Y | 30 | 205 | physical, identified | a43_closing_s126.md:50 (205.3); IV fit 163-166 | firmware 6.8x low; derived vs fit -20 % open (A-44) |
| MC_INDI_G2_Y | 0 | 27 | physical, identified | D-G2Y-DERIVE, g1.params:9 | J_r 5e-6 ASSUMED; UNVERIFIED |
| MC_INDI_K_R | 20 | 20 | bandwidth gain | yaml; bench 20 | halved to 10 pre-ident |
| MC_INDI_K_P | 20 | 20 | bandwidth gain | yaml; bench 20 (K_P not in grep, UNVERIFIED) | halved to 10 pre-ident |
| MC_INDI_K_Y | 10 | 10 | bandwidth gain | yaml; bench 10 | halved to 5 pre-ident |
| MC_INDI_ACT_TC | 0.05 | 0.033 | physical, identified | ref_airframe_model.md:22 tau 33 ms | UNVERIFIED tau->ACT_TC; bench used 0.02 and 0.05 |
| MC_INDI_LEAD | 1 | 1 | switch | yaml; bench 1 (5), 0 (2) |  |
| MC_INDI_DELAY | 0 | 0 | physical, computed | ident_concept.md:15 computed from filters | UNVERIFIED value |
| MC_INDI_ERPM_DLY | 1 | 1 | physical, identified | yaml; bench 1 | identified by lag |
| MC_INDI_ERPM_TO | 0.02 | 0.02 | bandwidth/guard | yaml; bench 0.02 |  |
| MC_INDI_ACT_BLD | 1.0 | 1.0 | guard | yaml; bench 1.0 (3), 0.0 (1) | one bench run differs |
| MC_INDI_DT_MAX | 1.0 | 1.0 | guard | yaml; bench 1.0 |  |
| MC_INDI_LND_SLEW | 5.0 | 5.0 | guard | yaml |  |
| MC_INDI_ERPM_FRZ | 0.5 | 0.5 | guard | yaml; bench 0.5 |  |
| MC_INDI_SP_TO | 0.5 | 0.5 | guard | yaml |  |
| MC_INDI_YAW_CUT | 0 | 0 | bandwidth | yaml; bench 0 |  |
| MC_INDI_INJ_* | AX 0 AMP .02 TP 20 FMIN .5 FMAX 60 NP 3 DLY 5 PT 0 RAMP .05 | unchanged (AX 0) | switch / ident procedure | yaml; bench overrides per test | ident procedure sets band vs halved gains |
| MC_INDI_POS_EN | 0 | 1 | switch | yaml; bench 1 (8) |  |
| MC_INDI_POS_LPF/DLY/TB | 10 Hz / 1 / 1.0 s | unchanged | bandwidth gain | pos yaml | bench values not grepped, UNVERIFIED |
| MC_INDI_PINJ_* | AX 0 AMP .05 TP 20 FLO .2 FHI 8 NP 3 PT 0 DLY 0 | unchanged (AX 0) | switch | pos yaml |  |

## 2. Ident-status gate (before identification)
- Halve: MC_INDI_K_R 20->10, K_P 20->10, K_Y 10->5 (bandwidth gains, per D-IDENT).
- Override physical values with the conservative ident config: for quad5in G1_*, G2_Y, ACT_TC, W_MAX hold the derived values above; ident acceptance (i) requires the estimate to be start independent from G1 x0.5/x1/x2, so the firmware generic defaults stay unchanged and the quad5in file is the reference start. Overestimated G1 is the conservative side.
- UNVERIFIED: no ident-status parameter exists in either yaml (grep of both lists); name and gating code are still to be defined. Any halving of K_* in firmware is also not implemented.

## 3. Mismatches
- G1_R/P/Y firmware 320/210/30 vs bench/derived 1757/1640/205: generic defaults are 5-8x low for quad5in. Bench file supersedes them; INDI_G1_Y bench also saw 30 in one place (stale).
- G2_Y firmware 0 vs derived 27 (yaw bistable without it, A-25).
- W_MAX firmware 0 disables the measured-torque path; the airframe file does not set it (a43_closing_s126.md:22), bench overlays set 2700 in 3 places and 0 in 3.
- ACT_TC firmware 0.05 vs model tau 33 ms vs bench 0.02/0.05.
- G1_Y: derived 205 vs IV fit 163-166 (-20 %), kept 205 (a43_closing_s126.md:67).
- LEAD 0 and ACT_BLD 0.0 appear in single bench runs, differ from defaults.
