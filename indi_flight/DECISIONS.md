# Decisions

Each entry: decision, alternatives, reason, what would overturn it. Owner decisions (F-, O-) are not re-opened by
the orchestrator; if one looks like the cause of a bad result, ask the owner (`QUESTIONS.md`).

## Owner decisions (from MISSION.md and review section 0, 2026-11-15)

- **F-1 No PID fallback.** INDI runs alone. Robustness is shown by measured margins (G2) and the robustness
  campaign (G3). An oscillation detector that logs and reports is allowed as an instrument only.
- **F-2 Every mode.** The INDI stack serves manual, acro, altitude, position, hold, mission, return, land,
  take-off, offboard and their failsafes. Offboard-only is not the end state.
- **F-3 Generic design, one reference airframe.** Architecture for any quadcopter with eRPM telemetry plus a short,
  justified requirements list. Development and gate evidence on one 5-inch quadcopter of about 600 g, simulated
  from sourced data (stage 1). Other airframes (x500, ~1 kg, >5 kg) flown once at the end as an outlook (G6).
- **F-4 Archive.** `indi_project/` is never modified. Corrections go to `results/errata.md` and the new report.
- **F-5 PID is a reference, never a pass condition.** No gate is a ratio to PID.
- **F-6 The outer loop replaces `mc_pos_control`**, started instead of it by parameter, serving every mode it serves.
- **O-5** Actuator state from measured rotor speed, modelled fallback when telemetry is missing.
- **O-6** Inversion on u = omega^2.
- **O-11** Separate modules behind Kconfig, started from `rc.mc_apps` by parameter; `mc_rate_control`,
  `mc_att_control`, `mc_pos_control`, `control_allocator`, the control-allocation library and commander at zero
  diff against `main`.
- **O-12** Prune bad candidates early, abort bad runs.
- **O-13** A scenario is flown once with the reference controller before it enters a validation set.
- **Identified, never tuned:** physical parameters come from identification.

## Orchestrator decisions

Open, to be written before code (MISSION "Decisions that are yours"):
1. Outer-loop architecture (design project, `design/outer_loop_*`, owner confirmation before stage 5).
2. Steady command/output gap remedy per loop (also absorbs battery sag).
3. Identification concept on an unknown airframe, and behaviour before identification (owner question).
4. Airframe-independent defaults.
5. Yaw from measured rotor acceleration (after the simulator rotor inertia fix).
6. Filter matching at real rates.

### D-1 Reference airframe is a new gz model, not a re-parametrised x500 (2026-11-15)
- Alternatives: scale the x500 SDF parameters in place; use an existing PX4 small-quad model if one fits.
- Reason: every gate result is on this airframe; a separate model with its own sourced values table keeps the
  x500 untouched for the G6 outlook and makes each value traceable.
- Overturn: if an existing PX4 gz model already matches the 5-inch class within 20 % on every value of the table.

### D-2 Reference-airframe model lives in `indi_flight/sim/models/`, served via `PX4_GZ_MODELS` (2026-11-15)
- Alternatives: add it to `Tools/simulation/gz/models` (a submodule: PX4-gazebo-models, a change there is an
  upstream PR to another repo); generate it per run from x500 (the archive's `model_variant.py` approach).
- Reason: no submodule diff, versioned with the evidence, and the runner already overrides `PX4_GZ_MODELS` per run.
  A SITL airframe file (`ROMFS/.../init.d-posix/airframes/4xxx_gz_<name>`) is still needed to start it; it carries
  the `CA_*` geometry and is part of the firmware-side branch only if it is offered upstream (decide at stage 7).
- Overturn: if the overlay path breaks model resolution for nested includes, or upstream later wants the model.

### D-3 Reference-airframe simulation values after the second key (2026-11-15, session 2)
- Values: those of `design/ref_airframe_data.md` with the corrections of `design/ref_airframe_check.md`:
  maxRotVelocity 2700 (14.8 V loaded; battery sag is a later scale on it); rollingMomentCoefficient 5e-8
  (inertia-scaled from x500, keeps the effect at x500 relative size); rotor link izz 5e-5 (= 10 x J_r 5e-6, compensates
  rotorVelocitySlowdownSim 10 so the reaction torque is the physical J_r dw/dt), ixx=iyy 2.5e-5, subtracted from
  base_link; legs and collision box resized to a 5-inch frame; `SIM_GZ_EC_MIN` 0, `THR_MDL_FAC` 1 (exact
  linearisation since w = w_max s), `MPC_THR_HOVER` ~0.13.
- Alternatives: keep x500 rolling moment 1e-6 (20x larger relative disturbance); slowdown 1 (rejected: 446 Hz joint
  speed aliases at a 4 ms physics step); EC_MIN 150 or 600 (idle thrust 36 % of weight at 600, an ESC property the
  INDI loop sees only through telemetry; idle is added later as a plant variant if needed).
- Overturn: a gz run showing the rotor reaction torque does not scale as izz x d(w/10)/dt (sign or size), or J_r
  sources disagreeing by more than 2x once the web re-check is done (J_r is ASSUMED today).

## D-start-fallback (session 12, from review r3 R3-8)
- Decision: `rc.mc_apps` starts `mc_indi_rate_control` / `mc_indi_pos_control` with no `|| mc_*_control start`
  fallback when the INDI parameter is set. If an INDI module fails to start, the vehicle refuses to arm and reports why.
- Alternatives: stock fallback pattern (rejected: a silent PID fallback and a mixed INDI/PID stack, against F-1);
  announced fallback (rejected: F-1 forbids an escape route).
- Overturn: only by the owner (F-1).

## D-G1.6 (session 13): determinism criterion
- Decision: same-seed spread is bounded in absolute terms, against the gate thresholds that consume each metric, and every later verdict must exceed the measured spread (GATES.md G1.6 a-d).
- Alternatives: 2 % relative (rejected: ill-conditioned at the noise floor, 10-25 % on 3 cm deviations); bit-exact replay (needs lockstep between gz and PX4 and wall-clock-free MAVLink sends; out of reach unless T23 shows a cheap cause).
- Overturn: T23 (`design/determinism_s13b.md`) finds a single fixable cause that makes runs bit-identical, or the measured spread exceeds 10 % of a gate threshold.

## D-outer-arch (session 13): architecture A confirmed by the owner (Q1), plus A18 flatness feed-forward
- Decision: A (A1-A17, `design/outer_loop_candidates_r2..r4.md`). Owner asked to consider differential flatness
  (arXiv 1809.04048): A18 = jerk -> omega_ff side channel to the INDI rate module (`design/flatness_r1.md`, F-c).
  It is implemented after base A and kept only if a measured tracking gain exceeds the same-seed spread.
- Alternatives: F-a (no feed-forward), F-b (outer module runs the attitude loop, rejected: mode-dependent rate
  setpoint publishers).
- Overturn: review r5 finds a mode or edge that A18 breaks; tracking test shows no gain.

## D-G1.6-speed (session 14): batch speed factor = 4
- Choice: campaigns run at PX4_SIM_SPEED_FACTOR 4 (~40 s wall per 95 s sim run, one container).
- Alternatives: 1 (2.5x the wall time); 8+ (not tested, gz RTF on this host unknown).
- Reason: 30 same-seed runs (`design/g16_s13.md`): s4 means within the s1 same-seed spread on step and trajectory
  metrics, spreads of the same order.
- Overturned if: INDI runs show a speed-factor effect beyond the same-seed spread (A-4), or the s4 hover outlier
  (max_dev 0.063 m, run r5) turns out to be a speed-factor artefact.
