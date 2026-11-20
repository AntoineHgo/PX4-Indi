# Defaults audit (S138, offline): which inherited defaults lack evidence at the current value

Sources: src/modules/mc_indi_{rate,pos}_control/*_params.yaml, bench/params/quad5in_indi_defaults.params,
DECISIONS.md (D-DEFAULTS-FW l.668, D-KY l.739, D-RATE-LEAD addendum 2 l.285, D-RATE-BLD l.462), design/defaults_s127.md,
design/g2_verdict_s108.md, results/g2_rate_batch_s99, g2_attbreak_s107, stage5_s86_g2outer, stage5_s87_xy, stage5_s84_accbreak,
g2_yaw_ky20_s137. G2 evidence base flown with K_R/K_P 20, K_Y 10 (then firmware defaults), ACT_TC 0.050, LEAD 1, no ID_OK gate.
Only evidence at the exact current value is credited. Param-file contents were grepped, not every cell opened (UNVERIFIED for cells not listed).

| parameter | FW default | bench default | origin | evidence cell at this value | risk |
|---|---|---|---|---|---|
| MC_INDI_EN | 0 | 1 | chosen (switch) | all flights | none; FW 0 is a safe-off |
| MC_INDI_W_MAX | 0 | 2700 | derived (airframe SIM_GZ_EC_MAX), D-DEFAULTS-FW | S99 meas cells 2700; model-only cells (S100) 0 | MISMATCH; FW 0 = modelled-torque path, a different loop than all bench flights |
| MC_INDI_G1_R/P | 1757/1640 | same | derived (fit_s124 0.8 %), D-DEFAULTS-FW | S99 batch params 1757/1640 | G1 low is conservative; bigger-airframe outlook only (G6) |
| MC_INDI_G1_Y | 205 | 205 | derived, A-43/44 (IV fit 163-166, -20 % open) | S99 yaw cells (205) | 20 % open; sets yaw loop gain |
| MC_INDI_G2_Y | 27 | 27 | derived D-G2Y-DERIVE, J_r 5e-6 ASSUMED | S99 yaw cells (27) | assumed J_r; A-25 bistable if 0 |
| MC_INDI_ID_OK | 0 | 0 in file (runs set 1) | chosen, D-DEFAULTS-FW | none at 0 for G2 (D-DEFAULTS-FW overturn cond. "G2 at ID_OK 0" never flown) | FW default = K x0.5 = 10/10/10 effective, no margin cell; bench runs at 1 |
| MC_INDI_K_R, K_P | 20 | 20 | archive-carried, then D-RATE-LEAD (S48-53 model sweep: K20 PM 57 / GM 10.5 at 400 Hz; K40 fails) | S99 rate roll/pitch cells K 20, ACT_TC 0.05 (16 cells PASS); S107 attitude 6/6 | cells are at ACT_TC 0.05, not 0.033 (D-DEFAULTS-FW amendment flew hover/step only, no margins) |
| MC_INDI_K_Y | 20 | 20 | chosen S137, D-KY (was archive-carried 10) | results/g2_yaw_ky20_s137: 800 GM 18.8 / PM 78.4, 400 GM 14.4 / PM 81.9, 1 seed, rate-yaw only | attitude-yaw at K_Y 20 and 2nd seed not flown |
| MC_INDI_ACT_TC | 0.05 | 0.033 | identified (tau 33 ms) / FW kept 0.05, D-DEFAULTS-FW amendment | 0.05: all S99/S107 G2 cells; 0.033: G5 hover/step only (act_tc_s128), yaw ky20 s137 | MISMATCH; G2 margins at 0.033 for roll/pitch rate and attitude not measured; D-RATE-LEAD overturn is GM<6 dB if ACT_TC wrong by 40 % |
| MC_INDI_LEAD | 1 | 1 | chosen D-RATE-LEAD add. 2 (lead 0 gives PM 26) | S99, S107 cells at 1 | low |
| MC_INDI_DELAY | 0 | 0 | derived from filters, UNVERIFIED (defaults_s127) | none isolated | sets prediction in lead/inversion; value never swept |
| MC_INDI_ERPM_DLY | 1 | 1 | identified by lag | S99 meas cells (A-39 timing partial cross-check) | A-39 open on eRPM timing |
| MC_INDI_ERPM_TO / ERPM_FRZ / SP_TO / DT_MAX / LND_SLEW | 0.02 / 0.5 / 0.5 / 1.0 / 5.0 | same | archive-carried guards; FRZ, SP_TO, SLEW chosen in D-F7/D-FREEZE entries | stress cells (G3/G5 event scenarios) not itemized here: NONE credited | guards, not bandwidth; low unless the G3 event row hits them |
| MC_INDI_ACT_BLD | 1.0 | 1.0 | chosen D-RATE-BLD (S79), A-33 | S99 file ACT_BLD 1.0; A-33 stage5_s73 | low |
| MC_INDI_YAW_CUT | 0 | 0 | archive-carried | G5.1 K_Y 20 (YAW_CUT 0 in D-KY); G2 cells at 0 | 0 = off; low |
| MC_INDI_INJ_*, PINJ_* | AX 0 etc. | AX 0 | chosen (ident / G2 tooling) | n/a, off in flight | none |
| MC_INDI_POS_EN | 0 | 1 | chosen (switch) | G5, S87 | FW 0 = stock path; MISMATCH by design |
| MC_INDI_POS_LPF | 10 Hz | 10 | archive-carried (t122 S60) | S87 xy cells: params not showing POS_LPF (FW default applied implicitly, so value matches; not explicit) | sets accel-feedback lag in outer loop; weak confirmation |
| MC_INDI_POS_DLY | 1 | 1 | archive-carried (t122) | same implicit | same; unswept |
| MC_INDI_POS_TB | 1.0 s | 1.0 | archive-carried / key_k127 "OK" is range check only | S84 pt1.params, S86/S87 outer cells (TB 1.0; z PM 58-64, xy PM 49.7-64.8, GM >= 18 dB) | best covered of the outer set; xy PM floor 49.7 is only 5 deg over gate |

## Mismatches FW vs bench
EN 0/1, POS_EN 0/1 (intended switches). W_MAX 0/2700 and ACT_TC 0.05/0.033 are real behaviour mismatches: a user flashing the
firmware default runs the model-torque path with a 0.05 actuator and halved gains (ID_OK 0), a configuration with no G2 cell.
ID_OK 0 in the bench file with runs overriding to 1 is a latent trap (file as named is not the flown set).

## Parameters with no evidence at the current value, ranked by direct bandwidth / gate effect
1. K_R/K_P 20 at ACT_TC 0.033 (rate and attitude margins). Cheapest: the S99 rate roll cell, 800 Hz, seed 1, recipe results/g2_rate_batch_s99 on the G5 param base (same one-cell recipe as g2_yaw_ky20_s137).
2. Firmware-default effective config (ID_OK 0: K 10/10/10, W_MAX 0, ACT_TC 0.05). Cheapest: G2 model-only cell (g2_rate_modelonly_s100 recipe, W_MAX 0) with ID_OK 0, roll 800 Hz.
3. Attitude loop at K_Y 20 (D-KY overturn item). Cheapest: g2_attbreak_s107 ax3 (yaw) r800 s1 cell.
4. POS_LPF, POS_DLY (outer accel-feedback filter and delay, set implicitly). Cheapest: stage5_s87_xy one xy cell at PINJ_PT 0 with explicit values (PM floor 49.7 deg, thin).
5. DELAY 0 (computed value, not swept). Cheapest: any S99 roll cell re-run with DELAY at the computed value; else covered by item 1.
6. G1_Y 205 vs fit 163-166 and G2_Y J_r assumption. Cheapest: the S99 yaw 800 s1 cell already at 205/27 (GM 21.5), so margin covered; accuracy question stays A-44.
7. Guards (ERPM_TO/FRZ, SP_TO, DT_MAX, LND_SLEW). Cheapest: the existing G3/G5 event scenarios that trigger them; no new cell.
