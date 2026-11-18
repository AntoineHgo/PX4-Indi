# T206 library mutation tests + pre-update gate (T205 f1-f5, e2)

Tests added in `src/lib/indi_accel_control/IndiAccelControlTest.cpp` (fixture IndiAccelZOnlyTest), 5 new (47 total). All run in Docker
(`indi_project/docker/run.sh 'make tests TESTFILTER=IndiAccelControl'`); each mutation applied to indi_accel_control.cpp, run, then
`git checkout --` of the library source (final `git diff --stat src/lib/indi_accel_control`: test file only).

| item | test | mutation | result (new test failing) |
|---|---|---|---|
| 1 | TiltedClosedLoopStateConsistentWithNorm (30 deg, plant scale 0.85, 800 cycles, per-cycle thrust == |t_c|/g_t) | _thrust_prev from abs(t_c z) | FAIL |
| 1 | same | output thrust from abs(t_c z) | FAIL (plus 3 older tests) |
| 2 | InvalidThrustDirLeavesNoState (3 bad calls with other f_b/mean_u/a_ref, then 3 valid == fresh controller, real LPF + blend) | guard after state (lpf_f applied before return false) | FAIL |
| 3 | ThrustDirGuardThresholds (ratio 0.08 rejected, 0.12 accepted, scale-free, norm 1e-8 rejected) | 0.1 -> 0.06 | FAIL |
| 3 | same | 0.1 -> 0.15 | FAIL |
| 3 | same | n_norm < FLT_EPSILON test deleted | FAIL |
| 4 | VerticalFloorAndMinCollective (a_ref z +30, 30 deg dir; c_min branch, thr_min=0 floor 0.1, level dir thrust == thr_min) | floor removed | FAIL (plus 1 older) |
| 4 | same | floor uses -kMinUpThrust without c_min | FAIL |
| 5 | VerticalDemandNotLimitedByThreeAxisTiltLimit (a_ref (30,0,-1), 50 deg stock dir; 3-axis path tilt limited to 0.7; z equals -(g+1) and equals 3-axis z) | 3-axis tilt block also run in z-only | FAIL (plus CollectiveLimitsApplyNoTiltLimit) |

Item 5 note: the 3-axis tilt limit scales only the horizontal part and keeps t_c z, and the collective limit on a z-only vector scales the
whole vector to c_max whether or not a vertical clamp precedes it. So a mutation that "limits t_c(2)" through the tilt or collective logic
changes no observable z output; only the tilt-of-direction effect is observable, and that is what the test asserts. Not a bug.

## Module (T205 e2)
`McIndiPosControl.cpp` gate before `_control.resetIntegral()`: now `want_indi && stageInputsFresh(now) && _f_b.isAllFinite() && _q.isAllFinite() && _q.norm() >= 0.5f`
(library validity conditions). `make px4_sitl_default` in Docker: OK (module compiled and linked). No unit harness for the module.

## Format
`Tools/astyle/fix_code_style.sh` on the 2 changed files: Unchanged.

## UNVERIFIED
- Module gate change: compile only, no SITL flight, no fault injection with NaN f_b / q.
- Mutation 5 variants that change z are not observable (see note).
