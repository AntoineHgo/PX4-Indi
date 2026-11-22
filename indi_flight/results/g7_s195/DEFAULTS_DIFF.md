# G7(c) firmware defaults vs validated configuration (S195)

Validated set: indi_flight/results/g5_freeze_s157/params.params (FREEZE-10 flights, per freeze10_s193/README.md and g2o_fly.sh).
Runner (bench/run_scenario.py:1000-1090): the file is read as an explicit overlay, applied with `param set` for every key it lists, and
merged over bench/params/quad5in_indi_g1.params (G1/G2/W_MAX 2700, identical to the file). Only MC_INDI_ID_OK uses setdefault 1, which is why
the file sets it explicitly. Keys not in the file stay at the firmware default (so "not set" rows are equal by construction).
Scope: gz_bridge module.yaml has no MC_INDI_* parameter (SIM_GZ_* only, sim plumbing, out of scope). In airframe 4040 the only INDI line is
`param set-default MC_INDI_W_MAX 2700`. No other ROMFS file sets MC_INDI_* (rc.mc_apps only reads MC_INDI_EN / MC_INDI_POS_EN).
Note: a separate firmware-default flight cell exists (g2_freeze_s160/params_fwdef_roll.params: ID_OK 0, W_MAX 0, ACT_TC 0.05), not the validated set.

## Mismatches and classification

| param | firmware | validated | 4040 sets it? | type | class |
|---|---|---|---|---|---|
| MC_INDI_ACT_TC | 0.05 | 0.033 | no | physical (motor time constant; yaml says round up when unsure; mapping tau -> ACT_TC marked UNVERIFIED in the params file) | ii |
| MC_INDI_ID_OK | 0 (halves K_*) | 1 | no | identification attestation for the airframe's G1/G2/TC, not a gain | ii |
| MC_INDI_W_MAX | 0 (measured torque off) | 2700 | yes, 2700 | physical (rotor speed at full thrust) | ii (equal once 4040 is loaded) |
| MC_INDI_EN | 0 | 1 | no | master enable switch, boot-selected | iii |
| MC_INDI_POS_EN | 0 | 1 | no | outer-loop enable switch | iii |

No gain (K_R/K_P/K_Y, XY_P, XY_VP, POS_TB, LPF) mismatches. G1_R/P/Y and G2_Y firmware defaults equal the validated values (reference-airframe values).

Caveat to flag to the owner: for a generic user of 4040 (yaml + airframe set-default), ACT_TC (0.05 vs 0.033) and ID_OK (0 vs 1, i.e. K at 0.5x)
still differ from the flown set, because 4040 does not set them. Class ii by nature, but if "defaults are the validated configuration" is
read as "4040 as shipped == flown set", the fix is two `param set-default` lines in 4040 (ACT_TC 0.033, ID_OK 1), or flying 0.05, the value in the fwdef cell. That is a decision, not made here.
The enable switches differ by design (stock default off); whether 4040 should turn them on is an owner decision.

## Full table and script output

Command (repo root): `python3 -I indi_flight/bench/g7_defaults_diff.py` (exit 0). Self-test: `python3 -I indi_flight/bench/tests/test_g7_defaults_diff.py` prints OK.

| param | firmware default | validated | airframe set-default | equal | equal with airframe | class |
|---|---|---|---|---|---|---|
| MC_INDI_ACT_BLD | 1.0 | 1.0 | - | yes | yes | - |
| MC_INDI_ACT_TC | 0.05 | 0.033 | - | NO | NO | ii |
| MC_INDI_DELAY | 0 | 0 | - | yes | yes | - |
| MC_INDI_DT_MAX | 1.0 | 1.0 | - | yes | yes | - |
| MC_INDI_EN | 0 | 1 | - | NO | NO | iii |
| MC_INDI_ERPM_DLY | 1 | 1 | - | yes | yes | - |
| MC_INDI_ERPM_FRZ | 0.5 | 0.5 | - | yes | yes | - |
| MC_INDI_ERPM_TO | 0.02 | 0.02 | - | yes | yes | - |
| MC_INDI_G1_P | 1640.0 | 1640 | - | yes | yes | - |
| MC_INDI_G1_R | 1757.0 | 1757 | - | yes | yes | - |
| MC_INDI_G1_Y | 205.0 | 205 | - | yes | yes | - |
| MC_INDI_G2_Y | 27.0 | 27 | - | yes | yes | - |
| MC_INDI_ID_OK | 0 | 1 | - | NO | NO | ii |
| MC_INDI_INJ_AMP | 0.02 | not set -> fw default | - | yes | yes | - |
| MC_INDI_INJ_AX | 0 | 0 | - | yes | yes | - |
| MC_INDI_INJ_DLY | 5.0 | not set -> fw default | - | yes | yes | - |
| MC_INDI_INJ_FMAX | 60 | not set -> fw default | - | yes | yes | - |
| MC_INDI_INJ_FMIN | 0.5 | not set -> fw default | - | yes | yes | - |
| MC_INDI_INJ_NP | 3 | not set -> fw default | - | yes | yes | - |
| MC_INDI_INJ_PT | 0 | not set -> fw default | - | yes | yes | - |
| MC_INDI_INJ_RAMP | 0.05 | not set -> fw default | - | yes | yes | - |
| MC_INDI_INJ_TP | 20 | not set -> fw default | - | yes | yes | - |
| MC_INDI_K_P | 20.0 | 20 | - | yes | yes | - |
| MC_INDI_K_R | 20.0 | 20 | - | yes | yes | - |
| MC_INDI_K_Y | 20.0 | 20 | - | yes | yes | - |
| MC_INDI_LEAD | 1 | 1 | - | yes | yes | - |
| MC_INDI_LND_SLEW | 5.0 | 5.0 | - | yes | yes | - |
| MC_INDI_PINJ_AMP | 0.05 | not set -> fw default | - | yes | yes | - |
| MC_INDI_PINJ_AX | 0 | 0 | - | yes | yes | - |
| MC_INDI_PINJ_DLY | 0 | not set -> fw default | - | yes | yes | - |
| MC_INDI_PINJ_FHI | 8 | not set -> fw default | - | yes | yes | - |
| MC_INDI_PINJ_FLO | 0.2 | not set -> fw default | - | yes | yes | - |
| MC_INDI_PINJ_NP | 3 | not set -> fw default | - | yes | yes | - |
| MC_INDI_PINJ_PT | 0 | not set -> fw default | - | yes | yes | - |
| MC_INDI_PINJ_TP | 20 | not set -> fw default | - | yes | yes | - |
| MC_INDI_POS_DLY | 1 | 1 | - | yes | yes | - |
| MC_INDI_POS_EN | 0 | 1 | - | NO | NO | iii |
| MC_INDI_POS_LPF | 10.0 | 10.0 | - | yes | yes | - |
| MC_INDI_POS_TB | 0.3 | 0.3 | - | yes | yes | - |
| MC_INDI_SP_TO | 0.5 | 0.5 | - | yes | yes | - |
| MC_INDI_W_MAX | 0 | 2700 | 2700 | NO | yes | ii |
| MC_INDI_XY_P | 1.2 | not set -> fw default | - | yes | yes | - |
| MC_INDI_XY_VP | 2.4 | not set -> fw default | - | yes | yes | - |
| MC_INDI_YAW_CUT | 0 | 0 | - | yes | yes | - |

mismatches: 5 (MC_INDI_ACT_TC:ii, MC_INDI_EN:iii, MC_INDI_ID_OK:ii, MC_INDI_POS_EN:iii, MC_INDI_W_MAX:ii)
G7(c) would pass (0 class (i) mismatches)

Unverified: "equal" uses numeric comparison against the yaml default; the validated file is the one named above, not each flight's applied params (run.json params_applied not cross-checked). Classes live in a dict in the script; unclassified mismatches count as class (i).

## Verdict

G7(c) would pass on the class (i) criterion (0 class (i) mismatches; 3 class ii physical/identification, 2 class iii switches), with the 4040 ACT_TC / ID_OK caveat above.

## S195 follow-up (orchestrator)
- MC_INDI_ACT_TC 0.033 added to airframe 4040 (commit "fix(airframes): set the INDI motor time constant"). Gate
  flights unaffected: the runner sets 0.033 from the params file.
- MC_INDI_ID_OK stays 0 in firmware and 4040 by design (D-G7-DEFAULTS): it is the pre-identification state (D-IDENT,
  gains at 0.5x) that G6 must validate; the validated identified set is 4040 + ID_OK 1 after identification.
- MC_INDI_EN / MC_INDI_POS_EN stay 0: PID is the default (deliverable 1).
