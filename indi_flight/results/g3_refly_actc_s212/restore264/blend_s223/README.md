# Blend probes S223 on draw 264 `joint` (saturation 0.351 + weak motor 3 at 0.709)

Same recipe as `../falsifier_s222/README.md`: gate binary 903eae63, samples `../samples_joint`, speed 1, `G3_PARAMS=<file> g3_chain.sh start <dir> 24 24 --samples ... --allow-binary 903eae63...` (start output in `p*_chain_start.txt`). `p3.params`, `p4.params` = `p1.params` with `MC_INDI_ACT_BLD` edited (one line each; diff against g5_freeze_s157/params.params verified). One flight each, flown sequentially, no retries. Raw .ulg untracked. Tilt from `../scripts/tilt.py`, errors from `../scripts/post_fault_err.py`.

| | joint | P1 ACT_BLD 0.15 | P3 ACT_BLD 0.10 | P4 ACT_BLD 0.05 | P2 W_MAX 0 |
|---|---|---|---|---|---|
| param in log | ACT_BLD 1.0 | 0.15 | 0.10 | 0.05 | W_MAX 0 |
| fault t [s] | 58.23 | 58.82 | 58.77 | 58.88 | 58.86 |
| max tilt after fault [deg] | 86.7 | 53.5 (61.19) | 52.4 (61.01) | 45.4 (60.98) | 45.3 (66.22) |
| LOC (>60 deg for 0.5 s) | yes | no | no | no | no |
| G3 key1 / key2 | LOC | FAIL / FAIL (item2) | FAIL / FAIL (item2) | FAIL / FAIL (item2) | FAIL / FAIL (item2) |
| roll rate err mean / abs, 1 s [rad/s] | -2.74 / 2.80 | -1.29 / 1.31 | -0.94 / 0.95 | -0.59 / 0.70 | -0.24 / 0.68 |
| pitch rate err mean / abs | -2.40 / 3.29 | -1.22 / 1.82 | -0.85 / 1.57 | -0.61 / 1.37 | -0.28 / 0.88 |
| roll torque err mean / abs | -0.0343 / 0.0362 | -0.0146 / 0.0160 | -0.0108 / 0.0118 | -0.0071 / 0.0099 | -0.0026 / 0.0113 |
| pitch torque err mean / abs | -0.0323 / 0.0419 | -0.0139 / 0.0215 | -0.0101 / 0.0195 | -0.0073 / 0.0188 | -0.0024 / 0.0134 |
| measured torque in use | 1.00 | 1.00 | 1.00 | 1.00 | 0.00 |

## Item 2 (oscillation) line frequency and start time of first flagged window

| | key 1 | key 2 |
|---|---|---|
| P3 | p 2.0 Hz from 23 s (4 windows); q 2.0 Hz from 21 s (5); r no line | p 2.0 Hz from 24 s; q 2.0 Hz from 22 s; r none |
| P4 | p 2.0 Hz from 22 s (6 windows), second line 2.0 Hz from 30 s (3); q 2.0 Hz from 22 s (3); r no line | p 2.0 Hz from 23 s; q 2.0 Hz from 23 s; r none |

All flagged lines start about 35 s before the fault, so they are not caused by the fault or the blend change (PID joint also fails item 2 key 1, see ../falsifier_s222/README.md). Key 1 and key 2 fail on item 2 only; items 1 and 3 pass.

Caveats: single flights, flight-to-flight variation unknown; the joint column's window contains the divergence (see S222 README). Tilt falls monotonically with ACT_BLD (86.7, 53.5, 52.4, 45.4) but with n=1 per point this is a trend, not a fit. Settling or side effects of fast blend in other cases were not tested.
