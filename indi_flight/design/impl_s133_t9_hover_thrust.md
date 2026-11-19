# S133 T9: hover-thrust continuity in mc_indi_pos_control

## A2 check (no conflict)
A2 (outer_loop_candidates_r2.md:21-27, DECISIONS.md D-STAGE-STALE / :716) says hover thrust enters PositionControl by
setHoverThrust only and the stock integrator is reset, so that the INDI-stage a_ref = feed-forward + P/D exactly. The
reason applies to the stage path only. The code (McIndiPosControl.cpp ~975 and ~1015) already calls
resetIntegral() on every cycle where the stage is requested/ran; only in bypass the stock integrator runs and is the
thrust-gap compensation (comment at ~970). updateHoverThrust shifts only _vel_int(2); on stage cycles it is zeroed
before PositionControl::update (resetIntegral under want_indi), so a_ref is unchanged. No conflict; proceeded.

## PositionControl::updateHoverThrust semantics (PositionControl.cpp:75-92)
Stores the new hover thrust (clamped), then, if _acc_sp(2) is finite (previous cycle's setpoint), adds
(a_sp - g) * Th_old / Th_new + g - a_sp to _vel_int(2) so T = a_sp*Th/g - Th is the same before/after.

## Change
- New pure helper src/modules/mc_indi_pos_control/HoverThrustSync.hpp: syncHoverThrust(control, last, ht):
  first value or |ht-last| <= 1e-6 -> setHoverThrust, else updateHoverThrust.
- McIndiPosControl.cpp: the per-cycle setHoverThrust(ht) became syncHoverThrust(_control, _control_ht, ht); the
  init setHoverThrust (~637) kept and records _control_ht. The stage's own ht (runIndiStage argument) untouched.
- McIndiPosControl.hpp: member _control_ht{NAN}. CMakeLists: gtest HoverThrustSyncTest (include dir guarded by
  if(TARGET) since the target exists only in the test config).
- Nothing changed under src/modules/mc_pos_control.

## Tests
HoverThrustSyncTest.cpp: stock PositionControl in a bypass-like cycle (sinking 0.3 m/s, hold v=0), 200 cycles at ht 0.5,
then ht -> 0.6. With the shift: |dT| <= 1e-3 (measured 3.7e-4, the integrator keeps integrating, about 0.06 % of
thrust, gate is 2 % of hover). Companion test: plain setHoverThrust steps thrust by 0.125 (> 0.02).
Commands (all via indi_project/docker/run.sh): make tests TESTFILTER=HoverThrust ; make tests TESTFILTER=unit
-> 100% passed, 152 tests; make px4_sitl_default -> links bin/px4, rc 0.
Break-check: syncHoverThrust using setHoverThrust only -> continuity test FAILED (dT 0.1248 vs 1e-4 bound used at that
time); restored, passes.
astyle: Tools/astyle/fix_code_style.sh on the 4 changed/new source files: no change after final edit.

## Diff summary
 indi_flight/LEDGER.md                                | 1 +
 indi_flight/STATE.md                                 | 2 ++
 src/modules/mc_indi_pos_control/CMakeLists.txt       | 4 ++++
 src/modules/mc_indi_pos_control/McIndiPosControl.cpp | 4 +++-
 src/modules/mc_indi_pos_control/McIndiPosControl.hpp | 2 ++
 5 files changed, 12 insertions(+), 1 deletion(-)
(plus untracked HoverThrustSync.hpp, HoverThrustSyncTest.cpp; LEDGER/STATE edits are pre-existing/other)

## UNVERIFIED
- No SITL flight assertion (build-list T9 asked for one in bypass-in-flight HTE update); only the gtest on the
  helper plus compile. The call site wiring (flying edge / HTE valid switch) is not exercised in a flight.
- astyle result for the CMake/hpp was via fix_code_style.sh (reported Unchanged for 3 files; the new .hpp line not
  shown in the tail).
