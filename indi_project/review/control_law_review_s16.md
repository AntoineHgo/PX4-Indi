# INDI rate controller, independent control-law review (session 16)

Scope: `src/lib/indi_rate_control/indi_rate_control.{hpp,cpp}`, the integration in
`src/modules/mc_rate_control/`, the `MC_INDI_*` parameters and the unit tests, read fresh
and not anchored on `indi_project/plan/architecture.md`. No code was edited, built or run.

Severity scale: **bug** (wrong behaviour on a reachable path), **risk** (correct on the nominal
path, degrades or fails on a plausible one), **style** (readability, maintainability).
Each finding is marked **confirmed** (code path traced end to end) or **suspected** (reasoned
from the code, not traced to every consumer or not reproduced).

## 1. Incremental law: sign, units, filter matching, actuator state

## 2. Yaw path filters (MC_INDI_YAW_CUT on the rate error)

## 3. Numerical and operational edge cases

## 4. Boundedness, allocation, readability

## 5. Robustness to actuator time constant mismatch (5-7 Hz roll limit cycle)

## 6. Test coverage gaps

## Summary ranked by severity
