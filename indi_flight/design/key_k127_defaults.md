# K127 key: review of bench/params/quad5in_indi_defaults.params

Checked: name and range in src/modules/mc_indi_{rate,pos}_control/*.yaml; values against cited sources. No sims run.

| name | value | verdict | evidence |
|---|---|---|---|
| MC_INDI_EN | 1 | UNSOURCED | Not found in the yaml greps I ran (not range-checked); the comment says "master switch" only. |
| MC_INDI_W_MAX | 2700 | OK | Yaml: rad/s, 0..5000, default 0. Airframe 4040_gz_quad5in:49-51 SIM_GZ_EC_MAX* 2700; ref_airframe_model.md w_max 2700; g1.params:12. Only EC_MAX1-3 seen, EC_MAX4 not seen. |
| MC_INDI_G1_R | 1757 | OK | Yaml 0.001..5000 (default 320). a43_closing_s126.md:50 table gives 1757 from source and fit 1752-1768. |
| MC_INDI_G1_P | 1640 | OK | Yaml in range (default 210). Table gives 1639 and fit 1634-1649. Rounding of 1639 to 1640 is fine. |
| MC_INDI_G1_Y | 205 | OK, contested | Derivation 205.3 is correct for the plant as built (a43_closing_s126.md). Same table: IV fit 163-166 (-20 %), unresolved (A-43/A-44). Range OK. |
| MC_INDI_G2_Y | 27 | OK, J_r ASSUMED | Yaml 0..1000 (default 0). Recomputed: 205*5e-6/(2*1.9e-8*999) = 27.0; kQ = 0.01267*1.5e-6 = 1.9e-8 (consistent). J_r 5e-6 is flagged ASSUMED in ref_airframe_model.md. G2 tied to G1_Y: if G1_Y is wrong, G2_Y scales with it. |
| MC_INDI_K_R | 20 | OK | Yaml 1..100 rad/s, default 20. "Bench flew unchanged" not checked against a run file. |
| MC_INDI_K_P | 20 | OK | Same. |
| MC_INDI_K_Y | 10 | OK | Yaml 1..100 rad/s, default 10. |
| MC_INDI_ACT_TC | 0.033 | UNSOURCED (mapping) | Yaml 0.001..0.2 s, default 0.05. 33 ms is timeConstantUp/Down (ref_airframe_model.md:22), but the file itself says the tau-to-ACT_TC mapping is UNVERIFIED and bench flew 0.02/0.05, never 0.033. quad5in_variants_s109.md:15 changes the model tau, so the value is variant-specific. |
| MC_INDI_LEAD | 1 | OK | Yaml 0..1, default 1. |
| MC_INDI_DELAY | 0 | UNSOURCED | Yaml 0..4, default 0. Comment admits "computed, not identified, UNVERIFIED for non-bench filters". |
| MC_INDI_ERPM_DLY | 1 | OK | Yaml 0..4, default 1. Claimed M3 correlation lag not checked. |
| MC_INDI_ERPM_TO | 0.02 | OK | Yaml 0.001..0.5 s, default 0.02. |
| MC_INDI_ACT_BLD | 1.0 | OK (range not shown) | Name exists, seconds time constant; range not displayed in my grep. |
| MC_INDI_DT_MAX | 1.0 | OK | Yaml 0.01..1, default 1.0. |
| MC_INDI_LND_SLEW | 5.0 | OK | Yaml 0.5..100, default 5.0. |
| MC_INDI_ERPM_FRZ | 0.5 | OK | Yaml 0.1..5 s, default 0.5. |
| MC_INDI_SP_TO | 0.5 | OK | Yaml 0.05..2 s, default 0.5. |
| MC_INDI_YAW_CUT | 0 | OK | Yaml 0..100 Hz, default 0. |
| MC_INDI_INJ_AX | 0 | OK | Name exists; default 0 not shown in grep, 0 assumed "off". |
| MC_INDI_POS_EN | 1 | OK, comment wrong | Yaml default 0, reboot_required. File sets 1 under the comment "switches, off by default". |
| MC_INDI_POS_LPF | 10.0 | OK | Yaml 0..100 Hz, default 10.0. |
| MC_INDI_POS_DLY | 1 | OK | Yaml 0..4, default 1. |
| MC_INDI_POS_TB | 1.0 | OK | Yaml 0..5 s, default 1.0. |
| MC_INDI_PINJ_AX | 0 | OK | Name exists, bench-only injection; 0 assumed off. |

No OUT OF RANGE values found. No missing parameter names (all 26 found in the yaml).

## Findings

BLOCKING
- None for loading the file. G1_Y 205 vs IV fit 163-166 stays open (see MAJOR 1).

MAJOR
1. G1_Y 205 (and G2_Y 27 derived from it) is 20 % above the only identified value (163-166), and A-43/A-44 are unresolved. A flight with high yaw gain could over-correct. Keep, but mark provisional and expect to retune G1_Y and G2_Y together.
2. ACT_TC 0.033 was never flown. Bench ran 0.02 and 0.05, and the lead term uses K*ACT_TC, so 0.033 is an untested point. Either use a flown value (0.05 default) or flag the first flight as the test.
3. Header says "full-gain values; the ident gate halves K_* until identified". Nothing in the params file enforces this. Confirm the gate exists in code, or the file flies full K unprotected.

MINOR
1. J_r 5e-6 is ASSUMED; G2_Y inherits the uncertainty linearly.
2. DELAY 0 is computed, not identified, and only valid for bench filters.
3. Comment "switches, off by default" is wrong for POS_EN 1, and EN 1 is also a non-default.
4. Only EC_MAX1-3 seen in the airframe grep (output was head-limited); EC_MAX4 not seen.
5. "Bench flew unchanged" claims (K_*, LEAD, ERPM_*) cite no run file or line, so they are UNSOURCED beyond the yaml defaults.
