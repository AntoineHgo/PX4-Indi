# NOTES_D: chapter 3 (inner loop)

File: chapters/03_inner_loop.tex. Source: ../01_inner_loop_design.md. Firmware yaml checked: src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml.

## Sections covered
Problem and idea (placement, signals table, inner_loop diagram), rate law (nu, lead, inversion, yaw), actuator state (model, measured, switching), filters and matching, steady command/output gap (blend), saturation, ground handling, guards (telemetry, stuck speed, arming, rejected cycles, setpoint timeout), parameters table, rate-loop margins (g2_bode_rate figure).
Labels: fig:inner_loop, fig:bode_rate, tab:inner_io, tab:inner_params, sec:inner_*; equations eq:inner_*.

## Build
`build.sh --no-figs`: no errors, no overfull boxes, no undefined references. Chapter 3 spans pages 9 to 18 (about 9 to 18, see toc). Whole report: 32 pages.
No preamble change.

## Checked against firmware
All 21 parameter defaults in the table (yaml column) match the yaml. The "Reference" column (quad5in set) is taken from the markdown only (bench/params/quad5in_indi_defaults.params, not re-read).
kMeasValidCycles 20, kFaultHoldCycles 3, kMaxBlend 2 confirmed in src/lib/indi_rate_control/indi_rate_control.hpp.

## Discrepancies and unverified claims
1. Notation: the markdown writes t (torque) and the CAPTIONS use u. The chapter uses u for per-axis torque, and u_i = (Omega_i/Omega_max)^2 for the rotor state as in chapter 2 (eq:u_state). Eq. inner_meas writes the rotor-state vector as u_rot to avoid a clash. Notation choice only, no value changed.
2. The continuous form of the blend (eq:inner_blend, \dot b = ...) is my transcription of the discrete update in the markdown (3.4); the discrete form is also given. Equivalent for ts << tb.
3. Mass-0.8 weak-motor test: the markdown says "one motor at 0.8" with no unit; the chapter repeats "0.8" without interpretation. Source: md 3.4 (10.4 deg), tb 0 vs 1 numbers (0.25 rad/s vs 1.6e-5) come from a unit test named in md 3.4, not re-run.
4. Margins in section "Rate-loop margins": only the roll spot values (PM 46.9 deg at 1.72 Hz, GM 15.7 dB at 18.3 Hz, DM 75.5 ms). The markdown section 8 table also lists pre-freeze rows with PM 69 deg and an unexplained gap to 46.9 deg; the chapter leaves these to the analysis chapter. Cause of the difference is unestablished (md Unverified).
5. G2_Y = 27 depends on an assumed rotor inertia J_r (md Unverified); the IV fit of G1_Y (163-166) disagrees with 205. The chapter states G values as "derived from airframe data", without J_r. Consider a caveat in the limits chapter.
6. MC_INDI_ACT_TC: 0.033 equals the simulated motor time constant. The reference params file still has an UNVERIFIED comment, and the yaml text says "when unsure, round up" (md Unverified). Not repeated in the chapter.
7. MC_INDI_DELAY = 0 is valid only for the bench filter cutoffs (stated in an indinote); other IMU_* cutoffs unverified.
8. The chapter says the fallback without telemetry "is not validated for the whole flight envelope" and refers to the limits chapter (ch:limits) for it, and for the saturation plus weak-motor limit. Check that chapter 7 covers both.
9. Yaw: the effective-gain statement "half of the set value when ID_OK is 0" is from md 3.1 / section 6; the K_* defaults are 20, so K = 10 rad/s at default.
10. Wording "Generic values ... raise the loop gain by a factor of 5 to 8" comes from md section 7 (former generic G1 values 320/210/30); numbers of those values are not given in the chapter.
11. The md says the arming check applies "MC_INDI_ERPM_TO to the oldest sample" and also a fixed 20 ms bound; the chapter says "sample age above 20 ms" in the arming list and 0.02 s default in the telemetry list. Equal at default.
