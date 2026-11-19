# K130 second-key review: D-STAGE-STALE (uncommitted diff, S130)

No BLOCKING found.

MAJOR
- M1 Mode (a) is "model inversion" only in steady state. McIndiPosControl.cpp:236-238 feeds f_b = (0,0,-G c_prev) to the
  library, but the library t_f path (indi_accel_control.cpp:318-335) goes through the u delay line (_delay samples) while
  f_b has no delay: t_c = a_c - g + (t_f(c_{k-d}) - f_model(c_{k-1})). Not integrator-like (b frozen, u_in = u_model - b is
  consistent), but for d >= 2 the delay-difference recursion c_k + c_{k-1} - c_{k-d} = r has roots outside the unit circle
  without the LPFs; stability then rests on the LPF attenuation near Nyquist. Needs a sim check (stale acc in SITL, d = 2..4)
  or a delay-matched model f_b. Also t_f uses g_t*k_cmd, the model f_b uses G: equal only if g_t*k_cmd == G.
- M2 Entry/exit step of mode (a): _lpf_f holds measured history and jumps to the modelled value, so a_f steps by
  (measured - modelled) = hover-gap, drag, actual accel error. b is frozen, so no compensation. Exit reverses the step.
  Acceptable for short outages, MAJOR only if outages are expected to toggle (stale threshold 20 ms, no hysteresis).

MINOR
- m1 F-1 holds: want_indi true -> mode never Bypass (IndiStageMode.hpp:33-41), resetIntegral unconditional (Run, diff @351),
  _indi_active true in Hold so the post-stage resetIntegral also runs (cpp:971). No stock thrust path found. OK.
- m2 Hold with !_held_valid: yaw_sp from stock att_sp.q_d can be NaN (a_ref non-finite case) -> thrustToAttitude publishes a
  NaN quaternion (cpp ~300-311). Guard yaw_sp finite (else 0 or last yaw). Held values otherwise finite (storeHeld checks).
- m3 Hold only overwrites q_d, thrust_body, local thrust; other att_sp fields (yaw_sp_move_rate, reset counters) are stock.
- m4 Library state at resume from Hold: _thrust_prev equals the held thrust (storeHeld after each success), dt is the module
  dt, filters just stale (not reset): small step on resume, no t_prev problem. After a Hold that started from a bypass-held
  value, library was reset() with the same c: consistent. _last_thrust bookkeeping OK (cpp:304,310).
- m5 Injection: _injection.update runs only in can_run, so it freezes in Hold and keeps injecting during IndiModelAccel
  (loop-break data contaminated); stage_mode in status flags it. Instrument bit 64 (lib_ok_prev) now means "active incl. hold".
- m6 ALTCTL z_only: deriveZOnly unchanged logic; library false return (thrust_dir invalid) now goes to Hold, fine. Ground/takeoff
  bypass unchanged (computeWantIndi equals the old expression; bypass reset path untouched, plus storeHeld).
- m7 Frame check passed: body FRD specific force hover (0,0,-g); a_f = R f + (0,0,g) (indi_accel_control.cpp:313).
  mean_u_valid = fresh_esc && !model_acc, blend held (setBlendHold + !mean_u_valid freeze).

Tests (IndiStageModeTest.cpp): table matches the spec and would fail on Bypass-when-wanted (WantedIsNeverBypass, AllOkIsIndi)
and on Hold for stale-acc-only (AccelStaleOnlyIsModelAccel); argument order verified. Gap: pure header only, nothing exercises
runIndiStage (update false -> Hold, integral reset, NaN a_ref, no stock thrust published); add a peer test (McIndiPosControlTestPeer).
