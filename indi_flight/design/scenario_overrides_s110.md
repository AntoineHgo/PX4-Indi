# Scenario overrides for G3 (S110)

## What changed (all under indi_flight/bench, nothing under indi_project, no firmware)
- `scenario_overrides.py` (new, pure): `merge(sc, ov)` = shallow merge (each top-level override key REPLACES the scenario's key whole,
  input not mutated) + `validate`. Allowed keys: `thrust_sag{scale}`, `motor_fault{segment, motor|motors, thrust_scale}`,
  `erpm_loss{motor,start,end}`, `wind{steady,peak,dir_deg}`, `disturbance`, `dist_segment`. Unknown keys / fields, bad motor index,
  scale outside (0,1], segment names absent from the merged scenario's `segments`, erpm start not before end, `wind` without
  `disturbance == gust_x`, peak < steady: `ValueError`, run_scenario exits before any sim starts ("--scenario-overrides FILE: ...").
- `run_scenario.py`: `--scenario-overrides FILE.json`. Merged scenario used for the whole run; `run.json` gets
  `scenario_overrides{file, overrides, merged_keys, merged_hooks}`, and `disturbance.wind` when a wind dict is present.
  The `--sched` refusal of hook scenarios still looks at the UNMERGED scenario, so overrides can add hooks under `--sched`
  (needed by position-mode G3 draws). `sag_tick` no longer calls a `None` setpoint function (needed under `--sched`).
- `disturbance.py`: `gust_x(t, af, steady=3, amp=6, dir_deg=0)`, `wind_speed(t, steady, amp)`; CLI `--wind-steady`, `--wind-peak`
  (TOTAL peak, amp = peak - steady), `--wind-dir` (deg from world +x towards +y, where the air moves to; the gust_diag convention).
  Physics unchanged: world-frame force `c_drag*v*|v|` at the CoM plus the cop_z torque, ramp/hold/gust timing fixed (28 s). Direction
  needs no frame change: it only splits the same world-frame force in x/y. Defaults take the old code path (dir 0 -> (d,0,0)).
- `g3_run.py`: writes `g3_scenario_overrides.json` per run and passes `--scenario-overrides`. Applied now: `thrust_sag`
  (ramp over the whole scenario window, so `ramp_s` is not used), `saturation` (motor_fault all 4 motors step at the main segment),
  `weak_motor` (motor_fault one motor), `tel_loss` (erpm_loss from main segment to `hold`), `wind` (gust_x, profile starts at the main
  segment). Main segment = `traj` (o1_lemniscate) / `stick` (stick_zsine_o6). Still not_applied: `tel_frozen`, `g4_typical_noise`
  ("hook missing"), and `weak_motor` when saturation is also on (one motor_fault slot).

## Tests
- `python3 bench/tests/test_scenario_overrides.py`: 5 PASS (merge shallow/pure, 13 rejection cases, default gust bit-identical to the
  original stepwise arithmetic for 300 time points, parametrised gust, no shipped scenario gets wind flags).
- `python3 bench/tests/test_g3_run.py`: 7 PASS; new `test_overrides_applied_and_valid` checks all 200+pretest draws: overrides merge
  validly into the real scenario, values equal the draw, only tel_frozen/g4/weak-with-sat remain not_applied.
- Mutation: replaced `out.update(copy.deepcopy(ov))` by `out.update({})`: test_scenario_overrides failed (KeyError 'thrust_sag'); restored, PASS.
- No-overrides regression (offline): for gust_x, o3_lemniscate_gust, v2_sag_att, motor_loss_0, v2_drop_att `merge(sc, {}) == sc` and the
  injector argv extras are `[]`, so the spawned disturbance.py command is the old one; the `--sched` check and `meta` are unchanged without the flag.
  Not a flown bit-for-bit comparison.

## Check flight
`indi_flight/results/g3_overrides_check_s110/run` (overrides.json next to it): `hover`, indi, quad5in, `--sim v2`, rate 800, speed 1,
overrides: thrust_sag 0.85, disturbance gust_x from segment `hold`, wind steady 3, peak 5, dir 90. rc 0, exit_status ok, docker timeout 900 s.
- Wind: onset 55.441 s (= window start); disturbance.csv fy = 0.0662 N at profile t=5 s (equivalent 3.00 m/s, drag formula with CdA 0.012),
  0.1837 N at t=12.5 s (5.00 m/s total peak), fx = 0 throughout (direction +y as set). Vehicle roll mean 0.61 deg at 4-6 s
  (before onset -0.03 deg; predicted 0.0662 N / ~6 N weight = 0.63 deg). Position hold keeps the drift at ~0.02 m, so no drift number.
- Sag: run.json thrust_sag: 60 steps from 55.452 s, 0.9999 -> 0.8525 (final step 0.8525 at 84.9 s, window end 85.44 s; the 0.5 s staircase
  stops just short of 0.85). Thrust setpoint z (vehicle_thrust_setpoint) mean 0.1369 (first 2 s) -> 0.1592 (last 2 s), x1.163 vs 1/0.85 = 1.176.
  Hover held.

## UNVERIFIED
- esc_status rpm of motor 0 did not change (9529 -> 9539) although thrust command rose 16 %; I did not find out why (telemetry eRPM
  model vs SIM_GZ_THR_SC). The sag claim rests on the SIM_GZ_THR_SC step log plus the thrust-command rise, not on rotor speed.
- Overrides under `--sched` (all position-mode G3 runs) were not flown: hook timing relies on the runner's segment times while the
  schedule player owns the setpoints; the offset of the segment times to the player's trajectory start is not checked.
  motor_fault, erpm_loss and direction other than 90 deg were not flown either (only unit-tested).
- Drawn timing is not honoured: erpm loss is segment-granular (start of main segment to start of `hold`), gust offset and sag ramp_s unused.
- Frame of dir_deg: world frame (gz ENU as in gust_diag); not checked against heading/NED conventions beyond the +y force and positive roll above.
