# 5 mm altitude offset between G3 key 1 and key 2 (S186)

## Cause
Both keys use the same reference (logged trajectory_setpoint z) and the same window. They differ in the truth height:
- key 1 (bench/g3_checks.py `evaluate`): alt = mean(-z_truth) + z_sp, raw sim_ground_truth z, no alignment.
  Horizontal is also compared raw (docstring: "no alignment is applied").
- key 2 (bench/g3_checks_key2.py `load_run`): h = sgn*(z - z0), z0 = median of the first 800 truth samples (vehicle at rest on the ground).
Checked on run_007: truth z at rest is +0.005000 m (NED, constant: the vehicle rests 5 mm below the sim z=0 plane, gear compression).
Key 2 therefore reads 0.005 m higher on every position run (h = -z + 0.005). Attitude runs are ungated and unaffected (offset 0.0000).
It is not window edges, interpolation or the reference: hRMS agrees to 5e-5 m.

## Which is correct
GATES.md G3 item 3 says "altitude error of truth against the reference/setpoint" and does not define the zero of the height axis. Two readings:
1. Raw sim frame (key 1): setpoint z is in the estimator frame, treated as equal to the sim frame. run_007 alt -0.102 m, F (limit 0.10).
2. Ground-referenced (key 2): the estimator z origin is the start (rest) height, so truth is re-zeroed to its rest value. run_007 alt -0.097 m, P.
Evidence cannot separate them at 5 mm: on the ground run_007's setpoint/estimator z reads about +0.02 to +0.04 m (estimator noise/drift, bigger than 5 mm),
so the log does not show where the estimator's zero sits relative to truth to better than a few cm. Reading 2 is physically the more natural
(the estimator has no knowledge of the sim plane), reading 1 is consistent with the horizontal handling in key 1.
No code changed; no rescore_v4 produced. Agreement stays as in KEY2_ITEM3_S186.md: 20 of 21 item-3 verdicts, the one split is run_007
(and any run within 5 mm of the 0.10 / 0.20 limit; run_013 -0.103 / -0.098 passes in both only because key 1 gates at 0.10 on... see that table).

## Decision needed from the owner
State in GATES.md the zero of the truth height axis (raw sim z, or relative to rest height). If ground-referenced, key 1 needs the z0 alignment;
if raw, key 2 must drop z0 for item 3. run_007 flips between F and P with that choice.

## Key 1 after D-G3-ZREF
Key 1 (bench/g3_checks.py) item 3 now zeroes truth z to the median over the first 1 s (z_rest); self-test zref_rest_offset added (old code -0.005, new 0.000).
Re-run on run_000..019 + run_017_pid_s185 into rescore_v4/key1/ against rescore_v3/key2/: item-3 verdicts agree 21 of 21 (run_007 -0.0974 P both).
Altitude means identical to 1e-4 m on the 18 position-mode runs; largest difference 0.0050 m on attitude-mode runs 004/010/016 (key 1 0.005 vs key 2 0.000:
key 2 measures attitude-mode altitude about the window mean, ungated; key 1 still reports the rest-offset-referenced value, also ungated). No verdict affected.
