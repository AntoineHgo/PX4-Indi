# Pre-freeze r1 F3/F4/F5/F6 fix (D-PREFREEZE-R1), not committed

## Diff (src/, line numbers in current tree)
- IndiStageMode.hpp (end): shouldResetOnPosControlEntry, shouldResetOnHoldToRun, kStageDtMin/Max (0.002/0.2), stageIntervalOk, stageDt.
- McIndiPosControl.cpp: runIndiStage takes the true interval raw_dt; dt = stageDt(raw_dt), rate_ok = stageIntervalOk (interval > 0.2 s -> Hold, D-STAGE-STALE b live again).
  F3: pos-control rising edge sets _pos_entry_pending (vehicle_control_mode handler) -> in runIndiStage sets _indi_reset_pending and refreshes
  _held_* from current _q and measured collective (thrust_ned = R(_q)*(0,0,-c)); held invalidated if att/collective not finite.
  Hold -> run edge (_stage_was_hold) sets _indi_reset_pending. Main loop: raw_dt computed unclamped, stock dt keeps [0.002,0.04].
- McIndiPosControl.hpp: members _pos_entry_pending, _stage_was_hold.
- indi_accel_control.cpp/.hpp: comments only (F5 early-check comment, F6 reset() bumplessness with mean_u).

## F4 filter choice
Filter rate = round(1/dt) of the true interval (dt up to 0.2 -> 5 Hz), protected by the existing hysteresis
(>20 % deviation for 5 consecutive cycles) so jitter does not reconfigure setFilter. No smoothed interval added. Library kMaxDt 0.5 > 0.2: no other
assumption of dt <= 0.04 found in IPC stage code (stock consumers keep the clamped dt).

## Tests (IndiStageModeTest.cpp)
PosControlEntryEdgeRequestsReset, HoldToRunEdgeRequestsReset, SampleIntervalGate (0.3 s hold, 0.1 s run with dt 0.1, 0.001 -> 0.002, NaN hold).

## Break-check (helpers reverted, test run, restored)
- PosControlEntry: line 102 shouldResetOnPosControlEntry(false,true) Actual false, Expected true.
- HoldToRun: line 110 shouldResetOnHoldToRun(true,true) Actual false, Expected true.
- SampleIntervalGate: line 118 stageIntervalOk(0.3f) true, expected false; line 120 stageDt(0.1) 0.04 vs 0.1; NaN and selectStageMode asserts fail.

## Results
make tests TESTFILTER=Indi: 9/9 pass (IndiAccelControl, IndiStageMode, ...). px4_sitl_default builds. astyle fix_code_style run on the 6 files.
## Unverified
Wiring in McIndiPosControl.cpp (edge flags, held refresh) has no unit/SITL test; only the pure helpers are tested. No SITL flight run. Break-check of the IPC call sites not done.
