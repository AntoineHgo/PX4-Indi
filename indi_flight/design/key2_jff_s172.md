# Key 2 review, D-JFF-SOURCE (S172), uncommitted diff of src/

Verdict: spec met. No BLOCKING, no MAJOR.

## Checks
1. No jerk read: PASS. grep -i "jerk|j_ref" over src/modules/mc_indi_pos_control/ finds only
   McIndiPosControl.cpp:320 (in.j_ref = NaN), param names MPC_JERK_* (hpp:263-264, cpp:547-548, 614),
   the reset helpers (cpp:286-293, 414, 870-879), comments, and FailsafeSetpoint.hpp:40 (WRITES sp.jerk = NaN, no read).
   No _setpoint.jerk, no _j_ff left. The only other consumer of the library output is j_used / omega_ff (output side).
2. j_ref NaN on every path: PASS. It is assigned unconditionally at cpp:320 inside runIndiStage, the only
   place that builds an Input. First cycle, estimator reset (jerk history reset, cpp:286-293) and mode
   switches all go through that line, so none can bypass it.
   Library (indi_accel_control.cpp:156-190, 285-303): per axis, a_ff NaN -> a_valid false, history dropped,
   j_diff 0; first valid sample after that -> prev seeded, j_diff 0 (no spike on return, a NaN->value step is not
   differenced); change -> (da)/(time since last change), clamped +-50 (kMaxJerk); unchanged < 0.1 s (kJerkHold)
   -> hold; unchanged > hold -> 0; then _lpf_j (measurement filter cut-off); omega_ff clamp +-3 rad/s (kMaxOmegaFf).
   _a_ff = _setpoint.acceleration (cpp:1087), set after the takeoff-ramp edit (z = NaN, cpp:953) and the ground/failsafe
   edits, before the stage; it is the generator feed-forward only, not P/D feedback or the injection
   (feedback is a_c_pre_inject, cpp:198). Partial NaN (takeoff ramp z, hold) is handled per axis, so an axis
   going NaN gives j = 0 with no spike.
   Residual spike risk (same as before, not introduced): a real step in a_ff (e.g. ground sentinel 0,0,100 at
   cpp:960 -> real value at liftoff, or a generator accel discontinuity) gives j = +-50 clamped, filtered,
   omega_ff bounded to 3 rad/s. Bounded, decays after hold + filter. Unchanged by this diff
   (stock jerk was NaN on the ground, so the library difference was already used there).
3. MAVLink offboard: unchanged. Old code mapped zero or non-finite jerk to NaN; offboard jerk is 0 or NaN -> NaN
   already, now NaN by construction.
4. Dead code: none in the module (_j_ff member and mapping removed in hpp and cpp).
   MINOR: library still supports finite j_ref (and the test uses it); intended, but
   Output.jerk_from_difference is now always true from this module (check any logging that treats false as meaningful).
5. Test coverage (IndiAccelControlTest.cpp):
   - Constant a_ff, NaN j_ref -> omega_ff 0: PARTIAL. JerkBackwardDifferenceAndHold (l.679) checks j_used (not
     omega_ff) hold and, after a reset, 0 on a constant first sample; OmegaFfIndependentOfYawRate uses a finite j_ref.
     No test names a long-constant a_ff (> kJerkHold) giving j_used == 0 / omega_ff == 0. (MINOR, gap)
   - Step in a_ff -> bounded decaying omega_ff: NONE as a step. JerkBackwardDifferenceAndHold covers a 50 clamp
     (10 m/s^2 step) on j_used, JerkDifferenceFiltered (l.724) covers a ramp with a filtered onset.
     No test asserts omega_ff <= kMaxOmegaFf nor decay after a step. (MINOR, gap)

## Findings
- BLOCKING: none.
- MAJOR: none.
- MINOR McIndiPosControl.cpp:320: could add a static note/test that the module never passes finite j_ref; fine as is.
- MINOR IndiAccelControlTest.cpp (new): add StepInAffGivesBoundedDecayingOmegaFf and ConstantAffGivesZeroOmegaFf (NaN j_ref, > 0.1 s).
- MINOR hpp:325 / cpp:316 comments are accurate; consider noting a_ff step at ground-sentinel exit (cpp:960).
