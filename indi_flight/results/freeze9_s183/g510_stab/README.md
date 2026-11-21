# G5.10 stabilized full-scale part, freeze-9 (owner Q17 A, SAT part dropped per Q21)

Rule: no LOC; tilt <= MPC_MAN_TILT_MAX + 5 deg (limit 40.0 deg); no windup = attitude error to the
stick-commanded attitude <= 5 deg within 1 s after sticks return to centre. The 2.0 m alt-loss limit
is not applied (full throttle climbs, ~470 m gain). PID is reference only.

Command: `bash indi_flight/results/freeze9_s183/g510_stab/fly.sh <indi|pid> <seed>` (scenario
g510_stab_full, stabilized sticks; scorers key 1 = bench/g510_score_motors.py, key 2 = bench/g510_motors_key2.py).

| stack | seed | LOC | tilt_max (limit 40) | att_err at 1 s after centre | key 1 | key 2 | keys agree | exit status |
|---|---|---|---|---|---|---|---|---|
| INDI | 1 | no | 35.42 | 0.23 deg | PASS | PASS | yes | failed: wall timeout in 'land' |
| INDI | 2 | no | 35.50 | 0.22 deg | PASS | PASS | yes | failed: wall timeout in 'land' |
| INDI | 3 | no | 35.62 | 0.18 deg | PASS | PASS | yes | failed: wall timeout in 'land' |
| PID (ref) | 1 | no | 35.01 | 0.87 deg | PASS | PASS | yes | failed: wall timeout in 'land' |
| PID (ref) | 2 | no | 34.95 | 0.88 deg | PASS | PASS | yes | failed: wall timeout in 'land' |
| PID (ref) | 3 | no | 34.95 | 0.86 deg | PASS | PASS | yes | failed: wall timeout in 'land' |

Validity: all 6 runs report covered_span True and valid True. The scored window is about t=58-69 s;
every run failed only in the landing phase at sim t~670 s (slow landing after the several hundred
metre climb), long after the scored window, so the failure is outside it.

Verdict: INDI 3/3 PASS under both keys. PID reference also passes (not a pass condition).
