# S85 per-run hole reporter (G1 evidence limit 1)

Tool: `indi_flight/bench/hole_report.py`; self-test `indi_flight/bench/tests/test_hole_report.py` (numpy only).

## Usage
    python3 indi_flight/bench/hole_report.py <run_dir|flight.ulg> [--out report.json]   # exit 0 PASS, 1 FAIL, 2 no topics
    python3 -I indi_flight/bench/tests/test_hole_report.py

## Design
- Core `analyse(topics, t_start, t_end, dropouts)` works on timestamp arrays; pyulog only in `load_ulog`.
- Nominal period = per-topic median (after the first second). Gap = interval > 1.5 x median. Missing = round(dt/median)-1.
- Classes: logger (gap overlapping a ULog dropout; counted from dropout records), sim (gaps in sim_ground_truth,
  sensor_gyro), controller (vehicle_angular_velocity, vehicle_torque_setpoint, actuator_motors, and the outer-loop
  vehicle_local_position_setpoint at its own ~89 Hz median) that no sim hole overlaps (+- 1 period).
- Limits (G1.1): missing fraction sim <= 0.05 %, controller/logger <= 0.1 %; single hole (gap dt) <= 10 ms.
  Class count = max over its topics (one hole seen in several topics counts once); verdict = worst topic.
- Two things found on real data and handled, both visible in the code docstring:
  1. Controller topics carry duplicate stamps (dt = 0, ~1000 per 66k samples in indi_posctl) paired with 2.5 ms gaps:
     publisher jitter, no sample lost (counts equal gyro count within 1). A one-sample gap within 8 samples of a
     duplicate cancels it. Without this, the 800 Hz run showed a false 0.4-0.8 % controller holes.
  2. `*_groundtruth` topics other than sim_ground_truth are logged at ~88 % of step rate in that run. They are reported as
     class `sim-info` and excluded from the verdict when sim_ground_truth exists (sim_ground_truth shows 0 holes).
- trajectory_setpoint is event-driven (42 Hz, irregular), so it is NOT a rate topic and is not analysed.

## Test evidence
All 20 checks pass: no holes at 800 and 400 Hz (rate from median), 89 Hz outer topic median, sim hole propagated to
controller topics counted as sim only (and the same sim hole in 2 sim topics counts once), controller-only hole,
12 ms controller and sim holes FAIL, 5 ms hole passes, first second ignored, logger dropout counted as logger, 15 ms
dropout FAIL, duplicate+gap cancel, decimated groundtruth info only.
Break check (once, restored): removing the sim-overlap clause from the controller filter failed
"sim hole not counted as controller" and "12 ms sim hole FAIL"; restored, ALL PASS.

## Real runs (outputs: hf.txt/.json, indi_posctl.txt/.json in this directory)
### stage5_s84_accbreak/hf (rate_hz 400)
```
hole report: ../results/stage5_s84_accbreak/hf/flight.ulg  (span 110.9 s after the first second)
topic                                 class       rate Hz holes  miss   miss %  max ms  verdict
sim_ground_truth                      sim           400.0     5     5   0.0113    6.25  PASS
vehicle_attitude_groundtruth          sim-info      400.0     6     6   0.0135    6.25  info
vehicle_angular_velocity_groundtruth  sim-info      400.0     6     6   0.0135    6.25  info
vehicle_local_position_groundtruth    sim-info      400.0     6     6   0.0135    6.25  info
sensor_gyro                           sim           400.0     1     1   0.0023    5.00  PASS
vehicle_angular_velocity              controller    400.0     1     1   0.0023    5.00  PASS
vehicle_torque_setpoint               controller    400.0     1     1   0.0023    5.00  PASS
actuator_motors                       controller    400.0     1     1   0.0023    5.00  PASS
vehicle_local_position_setpoint       controller     88.9     0     0   0.0000    0.00  PASS
CLASS sim        holes    5  missing 0.0113 % (limit 0.05 %)  max 6.25 ms (limit 10)  PASS
CLASS controller holes    1  missing 0.0023 % (limit 0.10 %)  max 5.00 ms (limit 10)  PASS
CLASS logger     holes    0  missing 0.0000 % (limit 0.10 %)  max 0.00 ms (limit 10)  PASS
OVERALL PASS
exit 0
```
### stage5_s83_stick/indi_posctl (rate_hz 800)
```
hole report: ../results/stage5_s83_stick/indi_posctl/flight.ulg  (span 81.6 s after the first second)
topic                                 class       rate Hz holes  miss   miss %  max ms  verdict
sim_ground_truth                      sim           800.0     0     0   0.0000    0.00  PASS
vehicle_attitude_groundtruth          sim-info      800.0  7615  7615  11.6626    2.50  info
vehicle_angular_velocity_groundtruth  sim-info      800.0  7698  7698  11.7898    2.50  info
vehicle_local_position_groundtruth    sim-info      800.0  7684  7684  11.7683    2.50  info
sensor_gyro                           sim           800.0     0     0   0.0000    0.00  PASS
vehicle_angular_velocity              controller    800.0     2     2   0.0031    2.50  PASS
vehicle_torque_setpoint               controller    800.0     2     2   0.0031    2.50  PASS
actuator_motors                       controller    800.0     2     2   0.0031    2.50  PASS
vehicle_local_position_setpoint       controller     88.9     0     0   0.0000    0.00  PASS
CLASS sim        holes    0  missing 0.0000 % (limit 0.05 %)  max 0.00 ms (limit 10)  PASS
CLASS controller holes    2  missing 0.0031 % (limit 0.10 %)  max 2.50 ms (limit 10)  PASS
CLASS logger     holes    0  missing 0.0000 % (limit 0.10 %)  max 0.00 ms (limit 10)  PASS
OVERALL PASS
exit 0
```

## Unverified / caveats
- hf: the sim hole (5 in sim_ground_truth, 1 more in sensor_gyro only) and the single 5 ms controller hole were not
  cross-checked against gz.log; the controller hole is not near a sim_ground_truth hole but may sit at a sensor_gyro one
  (sensor_gyro hole counted at the sim class only if it is outside logger dropouts; check by hand if it matters).
- Fractions use samples in the log as the denominator (missing/(missing+logged)); gate_g1.sh may use sim step counts.
- "Max single hole" is the sample-to-sample gap dt, so one lost 800 Hz sample reads 2.5 ms.
- Not run against gate_g1.sh numbers for the S24 runs; no logger dropouts occurred in either real run, so the logger
  path is verified on synthetic data only.
