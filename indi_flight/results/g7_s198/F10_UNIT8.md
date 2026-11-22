# F-10 unit 8: parameter yaml, INDI msg, rc.mc_apps, 4040_gz_quad5in, Kconfig (text only)

Baseline HEAD, edits left in the working tree, not committed. 8 files changed (140 insertions, 76 deletions). Diff of the unit: f10_u8.patch.
Files: both mc_indi_*_params.yaml, msg/IndiPosStatus.msg, IndiRateFeedforward.msg, IndiRateStatus.msg, ROMFS rc.mc_apps, 4040_gz_quad5in, mc_indi_pos_control/Kconfig (mc_indi_rate_control/Kconfig needed no change).

## Hits
Before: 13 lines (D-start-fallback/F-1, D-GAP, D-F7-GROUND, D-STAGE-STALE, A18, "gate" x3, "architecture A", indi_flight/ paths x2) plus "frozen" x1. After: 0 project hits. "frozen" (INDI_ERPM_FRZ short text, stuck rotor rpm) is physical and kept, as in unit 7.

## Changes
- mc_indi_rate_control_params.yaml: patch F_TEXT_PARTIAL_S196e.patch applied (git apply, 18 hunks: "Replaces MPC_*" wording removed, per-axis K_R/K_P/K_Y text, "half their value", normalised-torque wording, units). Then: all `long:` over 118 columns re-wrapped as `>-` folded blocks under 120 columns (one paragraph, no newlines reach QGC); LND_SLEW "maybe_landed alone does not slew" -> "A change of the maybe landed state alone does not start the ramp"; INJ_PT "gate reopens" -> "those conditions are met again", "control law has no fault" -> "INDI controller reports no fault"; ID_OK option 0 shortened below 120 columns; G2_Y last sentence reworded (too small harmless, too large reduces the stability margin).
- mc_indi_pos_control_params.yaml: PINJ_AMP, _TP, _FLO, _FHI, _NP got a `long:` (bench only, only used when MC_INDI_PINJ_AX is not 0); XY_P and XY_VP "Replaces MPC_*" -> "Used instead of MPC_* while mc_indi_pos_control runs" (XY_P also says what it is: velocity setpoint per unit of position error); long lines re-wrapped.
- msg: ids D-GAP, D-F7-GROUND, D-STAGE-STALE, A18, "freshness gate" removed; one-letter symbols (c, d, u, x, y, b, c_i) replaced by words; IndiRateStatus publisher corrected to mc_indi_rate_control (was mc_rate_control / MC_RATE_CTL_TYPE; verified in McIndiRateControl.hpp). `[@enum ...]` tags and field names/types untouched.
- rc.mc_apps l.59: id removed ("No fallback: if the INDI module fails to start there is no position controller"). 4040_gz_quad5in: "Model: quad5in, served through PX4_GZ_MODELS", indi_flight/ paths removed. Pos Kconfig: "(architecture A)" removed.

## Visible metadata changes (parameter text and unit, owner to confirm)
New `unit:` (reaches parameters.json and QGC): MC_INDI_G1_R, MC_INDI_G1_P, MC_INDI_G1_Y rad/s^2; MC_INDI_G2_Y rad/s; MC_INDI_LND_SLEW 1/s. Changed long text: 20 parameters; five new long texts in the PINJ group. No name, default, min, max, type, increment, decimal, option change.

## Checks (run from the repo root, docker only)
(i) Baseline: the 8 files at HEAD, `indi_project/docker/run.sh -n f10u8b -t 3600 'ninja -C build/f10_sitl metadata_parameters uorb_msgs'` (f10_u8_build_base.log), parameters.json and uORB/topics saved. New: same command with the edited files (f10_u8_build_new.log). Both rc 0. PASS.
(ii) parameters.json compare (f10_u8_params.log): 2188 vs 2188 parameters, same keys; default, min, max, type, increment, decimal, reboot_required, values identical for all; 23 parameters differ, all MC_INDI_*, only in `longDesc` (20) and `units` (5, listed above). PASS.
(iii) `diff -r` of the generated uORB/topics headers baseline vs new: empty (identical). PASS.
(iv) No C/C++ touched, so make format / astyle not applicable. YAML parse is covered by the successful metadata build. PASS.
(v) Project-id grep (D-*, A/S/F/G/K/Q ids, G7(x), owner, gate, freeze, indi_flight, indi_project, architecture A) over the 9 in-scope files: 0 hits except the physical word "frozen". PASS.

## Not verified
Full px4_sitl_default firmware build and the ROMFS/rc script were not run (text-only comment edits; rc.mc_apps and 4040 are not parsed for these lines). No flight.
