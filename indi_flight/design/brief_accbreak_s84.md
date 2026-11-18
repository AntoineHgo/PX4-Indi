# Brief T174 (S84): INDI acceleration-loop break at the stage OUTPUT (G2 + D-GAP HF half)

Model: sonnet. Budget ~30 tool calls. Write progress to `indi_flight/results/stage5_s84_accbreak/NOTES.md` as you go.

## Goal
G2 needs margins of the INDI acceleration loop itself (break at the plant input of that loop). Today
`MC_INDI_PINJ_*` (D-G2-PINJ, S82) injects d at the stage INPUT (u = c + d = a_ref): that measures the
velocity/position loop with the INDI acceleration loop closed. Add a second injection point at the stage OUTPUT.

## Known
- Module: `src/modules/mc_indi_pos_control/McIndiPosControl.cpp` lines ~180-235. Injector `IndiPosInjection`
  (`_injection`), params MC_INDI_PINJ_AX/AMP/TP/FLO/FHI/NP/DLY (module params yaml in the module folder).
- Library: `src/lib/indi_accel_control/indi_accel_control.cpp`. Output `out.t_c` (NED thrust-acceleration vector,
  m/s^2; published normalised as t_c / G), `out.thrust` (collective). The model path of the D-GAP blend uses
  `_thrust_prev = thrust` (line ~383): u_model = _thrust_prev * _k_cmd.
- Analysis: `indi_flight/bench/pinj_csv.py` (+ its self-test under `indi_flight/bench/tests/`) computes
  L = -G_cd/G_ud from `indi_pos_status` fields `a_c_pre_inject` (c) and `a_c` (u). Previous run and its exact
  commands: `indi_flight/results/stage5_s83_velbreak/README.md` (copy its flight command, TB 1.0, DLY 20, NP 5).

## Specification
1. New int param `MC_INDI_PINJ_PT` (0 = stage input, current behaviour, default; 1 = stage output). Bench only,
   documented as such, same style as the other PINJ params.
2. PT = 1: a_ref = c unchanged (no input injection). After `_indi.update`, controller output c_o = out.t_c;
   applied u_o = c_o + d on the selected NED axis. The applied vector u_o is what goes to thrustToAttitude and
   local_pos_sp.thrust. The library must see the APPLIED collective as its previous command (the model path models
   the actuator, which receives u_o): add a small library method (e.g. `setAppliedThrust(float)`), called only when
   PT = 1 and the injector is active, setting `_thrust_prev` to |u_o|/G (same clamping as the library applies to
   thrust). Without injection nothing changes (AX = 0 or PT = 0 must be bit-identical in behaviour).
3. Logging: add to `indi_pos_status.msg` what the analysis needs to form c_o and u_o at full rate without
   ambiguity (e.g. `t_c_applied[3]`, or a `pinj_point` field; t_c is already there). Keep uORB naming rules
   (`.github/instructions/*.instructions.md` matching `msg/**` and `src/**`).
4. `pinj_csv.py`: option `--point output` that uses c = t_c, u = t_c_applied (same L = -G_cd/G_ud). Extend its
   synthetic self-test with an output-point case with a known loop (must fail if c and u are swapped: check once).
5. Unit test in the library test file for the new method (break it once, confirm it fails, restore).
6. Build SITL in Docker (`indi_project/docker/run.sh`, see the S83 README for the build/flight commands), run the
   library unit tests, then ONE pre-test flight: z axis, PT 1, TB 1.0, same band and amplitude as S83 (lower AMP if
   the thrust saturates; say so). Report the measured L at each excited frequency, crossover, PM, GM if a -180
   crossing exists in band. Wall-clock timeout on every container; stop stray containers first.
7. `make format` on changed C/C++ (inside Docker if needed). Do NOT commit; list changed files in NOTES.md.

## Constraints
Do not touch mc_pos_control, mc_rate_control, mc_att_control, control_allocator, commander (zero diff). Raw logs
stay untracked. Flag anything unverified. Return a <=12-line summary: files changed, test results, the PM/GM and
crossover numbers, open items.
