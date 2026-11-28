# NOTES_E: chapter 4 (outer loop)

File: chapters/04_outer_loop.tex (pages 18-27 in the 02 build, 10 pages). Source: ../02_outer_loop_design.md. Firmware checked: src/modules/mc_indi_pos_control/mc_indi_pos_control_params.yaml, IndiStageMode.hpp, McIndiPosControl.{hpp,cpp}, FailsafeSetpoint.hpp, src/lib/indi_accel_control/indi_accel_control.hpp, stock MPC yaml files, airframe 4040_gz_quad5in.

## Sections
Problem and idea (tab:outer_io), acceleration law (frames, cascade, increment and thrust inversion, filters, saturation, jerk feed-forward), measured and modelled state (tab:outer_stage), steady thrust gap (blend), setpoint sources and modes (tab:outer_modes), ground/take-off/landing, resets and failure signals, guards, parameters (tab:outer_params), margins (forward reference to ch:analysis only).
Labels: fig:outer_loop, fig:outer_ground, tab:outer_io/stage/modes/params, sec:outer_{problem,law,cascade,inc,filters,sat,ff,state,gap,modes,ground,resets,guards,params,margins}, eq:outer_{fb,vsp,aref,inc,gt,cmd,ff,blend}.
Cross refs used: ch:inner_loop, ch:analysis, sec:indi_principle, eq:indi_law, eq:u_state (all exist). Margins table not reproduced (analysis chapter owns it).
Build: --no-figs, no errors, no undefined refs, no overfull/underfull warnings in main.log.

## Numbers checked (firmware)
- yaml: POS_EN 0, POS_LPF 10.0, POS_DLY 1 (0-4), POS_TB 0.3, XY_P 1.2, XY_VP 2.4, PINJ_* (8 params: AX, AMP, TP, FLO, FHI, NP, PT, DLY; md lists them as 6+2, text says eight), W_MAX default 0 (rate module yaml; pos module reads it, McIndiPosControl.cpp:56).
- Reference column: bench/params/quad5in_indi_defaults.params has POS_EN 1, POS_LPF 10.0, POS_DLY 1, POS_TB 0.3, W_MAX 2700. It does NOT contain XY_P/XY_VP; reference 1.2/2.4 comes from md (freeze file, "firmware defaults") = yaml defaults.
- Constants in indi_accel_control.hpp: kMaxBlend 0.5, kMeanUSatLimit 0.98, kMaxJerk 50, kMaxOmegaFf 3, kJerkHold 0.1, kMinUpThrust 0.1, kMaxDelaySamples 4, gravity 9.80665. kStageDtMin 0.002 / Max 0.2 (IndiStageMode.hpp). kStageMaxAge 20 ms, kAccRecoverTime 20 ms, ESC 100 ms, allocator 200 ms (McIndiPosControl). setFeedforward(true) at line 57. Ground acceleration 100 m/s^2 (cpp:959). Extrapolation cap 0.5 s (TRAJECTORY_STREAM_TIMEOUT_US 500 ms).
- Stock yaml: MPC_TILTMAX_AIR 45, LND 12, TKO_RAMP_T 3.0, TKO_SPEED 1.5, MPC_THR_MAX 1.0, XY_VEL_MAX 12 (not quoted in chapter). Airframe: MPC_THR_HOVER 0.137, MPC_THR_MIN 0.05.

## Disagreements / notes
1. MPC_THR_MIN: stock yaml default is 0.12; md table says 0.05 as "airframe". Chapter says 0.05 only "on the reference airframe" (airframe file confirms).
2. md says the freeze set sets MC_INDI_POS_EN 1 in a "freeze file"; the quad5in reference params file used here also gives 1. Consistent.
3. md and firmware agree on all other checked numbers. Not re-checked in firmware: 5.7 deg (derived, md Unverified), 0.3 m/s^2 blind descent, 200 ms fallback window, 1.9 deg yaw-reset tilt spike (decision record), 10 % edge step (gate verdict, not re-read), 95.7 -> 6.8 Hz alias (decision record), "about 267 Hz" accelerometer rate (md).
4. Removed on purpose: all D-/S-/G5 ids, line citations, file names, history of gains (1.9/3.6), drag feed-forward, bench rates r400/r800.
5. Notation: bold T = specific thrust (m/s^2), T_c in eq:outer_cmd = collective after thrust map (normalised), c = ||T_c||. The diagram uses T_c (non-bold) for the normalised collective, as in CAPTIONS.md; the text defines both. The diagram symbol u_i/u_meas,f/u_mod,f matches eq:outer_blend.
6. Blend rationale: md gives the 0.5 bound reason (thrust drop 0.36 in u units at hover loss, old bound 0.3); the chapter says only "large enough to absorb the thrust drop after a sudden loss of hover thrust", no number. Margin numbers (PM 62.7/67.3) deliberately left to the analysis chapter.
7. Table tab:outer_modes descriptions follow the control-mode flags in code (md says so); the requirements mode table has UNVERIFIED items (PositionTriplet flag set, Descend xy, external modes). Orbit/Follow listed as in md.
8. Unverified: whether the stage rate (not stated in text) matters; whether the reader needs the stage rate (88.9 Hz in md) - omitted.
