# A-14 closing test, part 1 (S21)

PID hover, quad5in, seed 1, speed 4, 800 Hz, build with `sim_ground_truth` (A-15 fix). r1-r3 with
`--log-from-start`, r4-r6 without. Residual = EKF z (`vehicle_local_position`) - truth z (`sim_ground_truth`),
`bench/a14_prearm.py` -> `prearm.md`; `bench/a14_check.py` on r1-r3 -> `a14_check.md`.

| run | log from boot | residual at arm [m] | pre-arm range [m] | max abs arm..+10 s [m] |
|---|---|---|---|---|
| r1 | yes | -0.008 | -0.030..0.028 | 0.170 |
| r2 | yes | -0.005 | -0.041..0.023 | 0.173 |
| r3 | yes | 0.042 | 0.017..0.051 | 0.074 |
| r4 | no (log starts at arm) | **-2.265** | n/a | 2.266 |
| r5 | no | 0.059 | n/a | 0.098 |
| r6 | no | -0.036 | n/a | 0.152 |

r4 at its first logged sample: EKF z -2.260 m with ref_alt 488.08 m, global alt 490.34 m, baro 487.51 m, truth
z 0.005 m (on the ground). So the EKF height state itself is 2.26 m high while landed; truth is fine. Rate so far
3 of 9 runs (S20 2/3, S21 1/6), 0/3 with boot logging, which is too few to link it to the logger.

Next: repeat with `--log-from-start` until one reproduces (expected ~1 in 3), then look at the pre-arm height
sources (sensor_gps alt, baro, estimator_status height innovations, EKF origin set time, the delayed-GNSS
model) to find which sensor pulls the height.

## Part 2: six more boot-logged runs (r7-r12)

Residual at arm -0.067..0.064 m, max abs arm..+10 s 0.094..0.215 m: none reproduces. Total so far: 0/9 with
`--log-from-start`, 3/6 without (S20 r0-r2: 2/3, S21 r4-r6: 1/3). If the two groups had the same rate, all 3
events falling in the 6-run group has probability C(6,3)/C(15,3) = 0.044. So the runner's path without boot
logging is now the main suspect (what it does before arm when the logger is not started early: parameter
application, logger restart, timing of the EKF origin relative to them). Next: read `run_scenario.py` for the
two paths (sonnet, read-only), then a pair test that changes only the suspected step.
