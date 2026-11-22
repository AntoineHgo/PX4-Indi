# Docs draft S201: open items for docs/en/config_mc/indi_control.md

## Uncertain statements (source lacked)

1. "The INDI controllers are designed to refuse to arm without rotor-speed telemetry" (R1 in airframe_requirements.md).
   No arming check was found by grep in the two module sources (only PX4_ERR start-up refusals, and a modelled fallback
   when telemetry is stale). Needed: the code path that blocks arming, or a corrected requirement. Wording is hedged in the page.
2. Identification procedure: the page says INDI flies its own excitation manoeuvre in a halved-gain configuration and the
   parameters are fitted afterwards. Lacking: who runs the fit (tool, script, on-board or offline), what the user does step by step,
   how the results are entered, who sets MC_INDI_ID_OK to 1 (manual?). The page carries an info note saying the tooling is not yet described.
3. Loop rate requirement: no source for a minimum rate of the rate and position loops, the IMU/gyro rate, or the
   acceptable ESC telemetry rate and latency. The bench checks are therefore qualitative. Needed: numbers.
4. Which flight modes/vehicle types are supported (multicopter only? VTOL?). The page says "every flight mode that uses mc_pos_control".
5. The build options: the board file option names come from Kconfig; the exact `boardconfig` flow and which production boards
   include them are unverified (only boards/px4/sitl/default.px4board enables them).
6. "Both modules must start before first arm" and "no stock fallback": from rc.mc_apps comments (position module) and R3; the rate module
   likewise has no fallback in the script, only a refusal if another publisher exists.
7. Whether INDI rate controller can be enabled without the INDI position controller (and vice versa): the scripts treat them independently; not stated as supported.
8. Bench check "status command of each module": not verified that both modules implement `status`.
9. Link targets `SENS_GNSS0_DELAY`, `MC_INDI_*` anchors in the parameter reference: not built or link-checked.
10. Prettier formatting and docs link checks were not run (shell was restricted); several table rows may need re-alignment.
11. Robustness limits: left as the TODO(owner) admonition.
12. G1 defaults are described only as "reference 5-inch quadcopter" values (yaml says so for G1_Y and G2_Y; G1_R and G1_P yaml do not say it).

## Parameter descriptions that look wrong or unclear

- MC_INDI_G1_R, MC_INDI_G1_P: description does not say the default is the 5-inch reference value (G1_Y does).
- MC_INDI_W_MAX: units "rad/s" but 5000 max; fine, but the description assumes thrust ~ omega^2 and does not say how to measure it.
- MC_INDI_LND_SLEW: no `unit:` field though the long text says normalised torque per second.
- MC_INDI_LND_SLEW long text: "maybe_landed alone does not slew" is internal wording, unclear to users.
- MC_INDI_G2_Y: the long text is very dense and does not explain how a user would estimate it.
- MC_INDI_INJ_PT: long text refers to a "gate" and "law has no fault", internal wording.
- MC_INDI_PINJ_AMP, _TP, _FLO, _FHI, _NP: no long descriptions (not marked bench-only unlike the INJ_* group).
- MC_INDI_PINJ_AX: Z axis labelled "Z (down)", ok; but amplitude unit m/s^2 given only in the AMP entry.
- MC_INDI_XY_P / MC_INDI_XY_VP: "Replaces MPC_XY_P" with no mention of the other MPC_* gains (vertical, limits) that remain in effect.
- MC_INDI_ACT_BLD, MC_INDI_POS_TB: "restores integral action" wording is jargon for users.
- MC_INDI_ID_OK: type int32 0/1 rather than boolean; the long text is clear.
