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
