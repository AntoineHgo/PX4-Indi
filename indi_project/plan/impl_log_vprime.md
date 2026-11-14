# V' (held-out set for v3) benchmark tooling log

Spec: bench/scenarios.md section 9 (W1-W5), implemented literally. No firmware, docs or git changes made.

## Step 1: read and implement
- Read bench/scenarios.py (SCENARIOS, _ATT, _V_PLANT), run_scenario.py (motor_fault hook ~l.455 and ~l.536, thrust_sag hook ~l.502),
  metrics.py (motor_fault_metrics), s2_verdict.py (PRIMARY map).
- Simulator question for W3: the T8 hook sets SIM_GZ_EC_MIN{m+1}/MAX{m+1}, one channel per motor, so a list of motors is
  just a loop over channels; no firmware/sim change needed.
- bench/run_scenario.py (motor_fault block): `motor_fault` accepts `motors=[...]` besides `motor=int`. Single-motor entries
  make the same get_param calls (MIN, MAX of the channel) and the same set_param calls (MIN, then MAX) in the same order,
  and run.json["motor_fault"] keeps the same keys/values. A list adds `motors`, `nominal_all`, `applied_all`
  (`motor`/`nominal`/`applied` describe the first motor).
- bench/scenarios.py (appended block "Stage-2 held-out set V'"): vp_loss1_06 (motor 1, 0.6, "loss", T8 segments),
  vp_loss2_08 (motor 2, 0.8, "loss"), vp_gain03_att (motors [0,3], 0.85, "up", _ATT), vp_sag75_att (thrust_sag 0.75, _ATT),
  vp_tau2_loss2_att (tau x2 model_variant as V1 + motor 2 at 0.8 from "up", _ATT).
- bench/metrics.py motor_fault_metrics: uses `motors` when present (faulty_* metrics over all weakened motors); single
  motor result unchanged (ks = [k]).
- Existing entries: SCENARIOS dict before vs after compared as JSON: all pre-existing entries identical (True), 5 new keys.
- Primary metrics: W1/W2 = window rotation-angle RMS (`attitude_tracking.rotation_angle_rms_deg`, as motor_loss_0 in s2_verdict),
  W3-W5 = `attitude_tracking.roll_rms_deg` (as v2_*_att). Both are already produced for these patterns.
- s2_verdict.py: NOT extended. TODO: it hard-codes the V entry set and the 10/14 threshold; a V' mode needs its own
  PRIMARY map (above) and thresholds 4/5 plus the --a/--b controller pair; not a small change.

## Step 2: regression check of metrics.py
Re-ran metrics.py on results/s2_heldout_v2/runs/motor_loss_0/indi_v2/seed1 (copy in scratchpad): motor_fault block bit-identical to the stored one.

## Step 3: harness checks (pid_tuned r1f c05, seed 1, speed 4, v2 config), sequential, -t 900
Containers present before flying (other project sims, untouched): px4-indi-v3sc-motor_loss_0-* (5). Flew only pid_tuned, seed 1.

### vp_gain03_att (W3), results/vprime_check/vp_gain03_att/pid_tuned/seed1/
- exit 0, run.json exit_status ok, wall 41 s, metrics.py exit 0, no warnings.
- run.json motor_fault: motors [0,3], thrust_scale 0.85, segment "up", event_us 48744000 (events: settle 46.744 s, up 48.744 s);
  nominal MIN/MAX 150/1000 on both channels; applied MIN 138, MAX 922 on both (SIM_GZ_EC_MIN1/MAX1 and MIN4/MAX4), omega_ratio 0.9220.
- metrics: roll_rms_deg 2.981, rotation_angle_rms_deg 3.036; motor_fault.attitude_rms_deg 3.265, peak tilt error 15.07 deg,
  saturation 0 s, motor_mean_faulty 0.697 vs others 0.605 (the weakened motors are commanded harder, so the fault is seen by the controller loop).

### vp_tau2_loss2_att (W5), results/vprime_check/vp_tau2_loss2_att/pid_tuned/seed1/
- exit 0, ok, wall 34 s, metrics exit 0, no warnings.
- model_variant: timeConstantUp 0.0125 -> 0.025, Down 0.025 -> 0.05 (tau x2 from the start, as V1).
- run.json motor_fault: motor 2, 0.8, segment "up", event_us 41933000; applied MIN 134, MAX 894 (nominal 150/1000), omega_ratio 0.8944.
- metrics: roll_rms_deg 3.191, rotation_angle_rms_deg 3.323; motor_fault.attitude_rms_deg 3.492, saturation 0 s, motor_mean_faulty 0.751 vs others 0.597.

## Open issues
- W1, W2 (T8 pattern, single motor) and W4 (thrust_sag 0.75) were not flown (budget of checks); they reuse unchanged hooks
  (W1/W2 differ from motor_loss_0 only in motor index/scale; W4 differs from v2_sag_att only in scale). Unverified in flight.
- s2_verdict.py has no V' mode (TODO, see Step 1).
- Files changed: bench/run_scenario.py, bench/scenarios.py, bench/metrics.py (all uncommitted).
