# S135 G5.4 take-off check (auto_smoke_check.py)

Implemented from the gate text: `takeoff_g54()` pure function (numpy arrays) plus wiring in `main()`; only fields
added (`out["g54_takeoff"]` in the JSON, 4 printed lines in the handover section). Existing outputs unchanged.

Definitions: collective = -vehicle_thrust_setpoint.xyz[2]; ramp start = first takeoff_status state 4; edge = 4 -> 5;
hover = mean collective over the hold phase (`win["hold"]` = takeoff_done..hold_end, existing helper). Step(t) =
|mean c[t,t+0.1) - mean c[t-0.1,t)|. Ramp points t_k = ramp_start + 0.5 + 0.1k for every t_k < edge (the last window
reaches past the edge, as the gate text says); edge step = Step(edge). Limit 10 % hover each. Dip: truth =
vehicle_local_position_groundtruth (already used by the checker), z_up = -z; dip = max(0, z_up(edge, interpolated)
- min z_up in [edge, edge+1 s]) <= 0.3 m. A ramp point with an empty window counts as failure (never silently skipped).

Self-test (4 gate cases + negative steps): smooth 3 s ramp (max step 3.33 % hover, 25 points), 15 % edge step fails,
15 % step at +1.0 s fails but at +0.3 s passes, 15 % drop fails (abs), 0.5 m dip fails.
Break-checks: dropping the 0.5 s offset made the "+0.3 s passes" test fail; dropping abs initially did NOT fail any
test (all steps were positive), so a negative-step test was added, and then dropping abs failed it. Both restored.
Host has no pytest: run with indi_project/docker/run.sh -n a135 -t 300 -- python3 -m pytest <test>  (5 passed).

Second key (f7_smoke_s134_fix/auto_tour): hover 0.1364; ramp 31.22..34.22 s, 26 points; max step 0.0103 = 7.5 %
hover at 31.82 s (matches README 0.0103 / 31.82 s); edge step 0.0060 = 4.4 % (README 4.5 %: README's number uses
indi_pos_status.thrust 0.1 s means; the gate and this check use vehicle_thrust_setpoint, 4.43 % vs 4.5 % is a signal
difference, not a bug); dip 0.000 m (README the same; README used vehicle_local_position, this uses groundtruth).
All three sub-criteria PASS.

## Follow-up: other G5.4 limits (`g54_other`)
All on vehicle_local_position_groundtruth (z_up = -z, relative to z_up at takeoff_cmd). Pure functions:
`takeoff_overshoot`, `touchdown_check`, `land_speed_check`, `descent_start`, `rtl_height_error`.
- Take-off target = MIS_TAKEOFF_ALT from run.json params_applied (the scenario's takeoff_alt is written there), else the
  ULog parameter. Overshoot = max z_up in [edge, takeoff_done+3 s] - target. Bounce = largest shortfall below target from
  the first time z_up >= target-0.2 m until hold_end (so it is >= 0.2 by construction when the target is reached from below).
- Touchdown contact = existing first ground_contact after rtl/land cmd; vz = mean over [c-0.2, c]; tilt from
  vehicle_attitude_groundtruth (fallback vehicle_attitude; source recorded in JSON), tilt = acos(1-2(qx^2+qy^2));
  re-lift and landed-drop checked in [contact, disarm].
- Land vz vs MPC_LAND_SPEED +-20 %; contact->disarm <= COM_DISARM_LAND (ULog param) + 1 s.
- RTL height: window rtl_cmd .. descent start; descent start = first time the trajectory_setpoint z_up falls 0.3 m below
  its running max since rtl_cmd (my choice; nav_state stays RTL(5) through the descent so it cannot mark it). "n/a" without
  an rtl phase. Error = max |truth z - setpoint z| at setpoint rows.
- scenarios.py: `auto_rtl20` = auto_tour with mission [(20,0),(20,20)] (RTL starts ~28 m from home); not run yet.
Break-check: forcing relift_ok True made test_g54_touchdown fail (8 tests pass restored).
Run on f7_smoke_s134_fix/auto_tour: overshoot -0.080 m (peak 4.92 m) PASS, bounce 0.200 m PASS; touchdown at 91.54 s:
vz -0.001 m/s, tilt 0.45 deg, re-lift 0.000 m, landed stays true, all PASS; land vz 0.702 vs 0.700 PASS, contact->disarm
2.68 s vs 2.0+1 PASS; RTL height error 0.029 m over [78.5, 84.3] s PASS.
Caveat: vz at contact ~0 suggests ground_contact is flagged after the vehicle has stopped (detector lag), so the 0.8 m/s
criterion is weak on this log.
Touchdown re-anchored on truth (replaces the ground_contact anchor above): ground = truth z_up at takeoff_cmd; t_td = first time
after the altitude maximum in [rtl/land cmd, disarm] with z_up <= ground+0.05 m; vz = max truth vz in [t_td-0.2, t_td]; tilt window
from t_td-1 s; re-lift = max z_up in [t_td, disarm] - ground <= 0.15 (reads ~0.05 by construction); ground_contact->disarm unchanged.
Test: late ground_contact (t=5.6) with a 1.2 m/s impact at truth touchdown is still caught; 8 passed. f7_smoke_s134_fix: t_td 91.10 s
(contact 91.54), vz 0.702 (was -0.001 with the old anchor), tilt 0.47 deg, re-lift 0.050 m, all PASS.
