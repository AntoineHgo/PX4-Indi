# Docs draft S201: open items for docs/en/config_mc/indi_control.md

## Uncertain statements (source lacked)

   RESOLVED S213: no arming check exists. grep of src/modules/mc_indi_*/ and src/ outside the modules finds no health/arming-check hook (no health_report, no commander reference); the only refusals are init() in McIndiRateControl.cpp:70-77 (another torque publisher) and the stale/missing esc_status fallback to the actuator model (McIndiRateControl.cpp:184-232, McIndiPosControl.cpp:133-165, 213). Requirement R1 in indi_flight/design/airframe_requirements.md is NOT enforced by code (design file left unedited). Page now says arming is not blocked.
1. "The INDI controllers are designed to refuse to arm without rotor-speed telemetry" (R1 in airframe_requirements.md).
   No arming check was found by grep in the two module sources (only PX4_ERR start-up refusals, and a modelled fallback
   when telemetry is stale). Needed: the code path that blocks arming, or a corrected requirement. Wording is hedged in the page.
2. Identification procedure: the page says INDI flies its own excitation manoeuvre in a halved-gain configuration and the
   parameters are fitted afterwards. Lacking: who runs the fit (tool, script, on-board or offline), what the user does step by step,
   how the results are entered, who sets MC_INDI_ID_OK to 1 (manual?). The page carries an info note saying the tooling is not yet described.
3. Loop rate requirement: no source for a minimum rate of the rate and position loops, the IMU/gyro rate, or the
   acceptable ESC telemetry rate and latency. The bench checks are therefore qualitative. Needed: numbers.
   RESOLVED S213: multicopter only. rc.mc_apps:14-62 is the only script that starts the modules (no rc.vtol_apps reference); McIndiRateControl.cpp:424 resets unless VEHICLE_TYPE_ROTARY_WING; pos module only has an unused-by-script 'vtol' start arg (McIndiPosControl.cpp:1257-1262). Pos stage runs only while armed with pos/vel/climb control (IndiStageMode.hpp computeWantIndi), else bypass.
4. Which flight modes/vehicle types are supported (multicopter only? VTOL?). The page says "every flight mode that uses mc_pos_control".
   RESOLVED S213: CONFIG_MODULES_MC_INDI_RATE_CONTROL (src/modules/mc_indi_rate_control/Kconfig:1, depends on MODULES_CONTROL_ALLOCATOR) and CONFIG_MODULES_MC_INDI_POS_CONTROL (src/modules/mc_indi_pos_control/Kconfig:1, depends on MODULES_MC_POS_CONTROL); only boards/px4/sitl/default.px4board:44-45 enables them, no production board does. Page says so.
5. The build options: the board file option names come from Kconfig; the exact `boardconfig` flow and which production boards
   include them are unverified (only boards/px4/sitl/default.px4board enables them).
   RESOLVED S213: ROMFS/px4fmu_common/init.d/rc.mc_apps:17-22 (MC_INDI_EN 1 -> mc_indi_rate_control start, else mc_rate_control) and :57-62 (MC_INDI_POS_EN 1 -> mc_indi_pos_control start, else mc_pos_control); comment at :59 'No fallback'. Rate module refuses start if another torque publisher <500 ms old (McIndiRateControl.cpp:70-77); the pos module has no such check. Page reworded to 'each enabled module'.
6. "Both modules must start before first arm" and "no stock fallback": from rc.mc_apps comments (position module) and R3; the rate module
   likewise has no fallback in the script, only a refusal if another publisher exists.
   RESOLVED S213: yes both ways, the two start blocks in rc.mc_apps:17 and :57 are independent. Not tested in flight; page states they are started independently and designed to be used together. Pos module jerk feed-forward is meant for the INDI rate module (McIndiPosControl.cpp:56) but nothing enforces the pairing.
7. Whether INDI rate controller can be enabled without the INDI position controller (and vice versa): the scripts treat them independently; not stated as supported.
   RESOLVED S213: both modules use PRINT_MODULE_USAGE_DEFAULT_COMMANDS (McIndiRateControl.cpp:546, McIndiPosControl.cpp:1311) and neither overrides print_status, so 'status' only prints the ModuleBase default 'running' (module_base.cpp:73). Page bench-check line fixed accordingly.
8. Bench check "status command of each module": not verified that both modules implement `status`.
   RESOLVED S213: every MC_INDI_* parameter named in the page exists in mc_indi_rate_control_params.yaml / mc_indi_pos_control_params.yaml (all 24 table rows checked, none missing); SENS_GNSS0_DELAY is generated from src/modules/sensors/vehicle_gps_position/module.yaml:72 (SENS_GNSS${i}_DELAY) and has an anchor in docs/en/advanced_config/parameter_reference.md. Link style matches other config_mc pages. Fixed MC_INDI_LND_SLEW unit to 1/s (yaml:205). Link check itself still not run (MC_INDI_* anchors appear only after parameter_reference.md is regenerated).
9. Link targets `SENS_GNSS0_DELAY`, `MC_INDI_*` anchors in the parameter reference: not built or link-checked.
10. Prettier formatting and docs link checks were not run (shell was restricted); several table rows may need re-alignment.
11. Robustness limits: left as the TODO(owner) admonition.
   RESOLVED S213: yaml defaults are now G1_R 1757.0, G1_P 1640.0, G1_Y 205.0, G2_Y 27.0 (mc_indi_rate_control_params.yaml:28-63), identical to bench/params/quad5in_indi_defaults.params, so the page statement is correct (limited to G1_*/G2_Y; ACT_TC and W_MAX are not reference values). Yaml long text of G1_R/G1_P still does not say 'reference 5-inch' (parameter-description list left as is).
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
