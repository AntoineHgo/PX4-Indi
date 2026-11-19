# S130b model f_b (fixes M1, M2, MINORs of key_k130)
## Signal reused (indi_accel_control.cpp, after edit)
- Old update(): f_b filter at l.311 (before the delay line), t_f from u at l.318-345: u_in (l.318) -> _u_buf ring (l.321) -> i_d (l.322) -> _lpf_u (l.323) -> u_f = u_meas_f + b -> t_f = z_b*(-g_t*u_f) (l.346-ish).
- New: delay line moved before the f_b filter. Invalid f_b: f_in = (0,0,-_g_t*(_u_buf[i_d] + b)), i.e. the SAME delayed element _u_buf[i_d] that feeds _lpf_u, same scale _g_t (u already includes k_cmd), plus the held blend b exactly as u_f adds it. Through _lpf_f (same cutoff as _lpf_u) -> cancels against t_f: t_c = a_c - g.
- u_valid = mean_u_valid && f_b_valid drives u_in (u_model - b when invalid), u_at_limit, blend_frozen (blend held inside the library). Input validation: allFinite(f_b) only required when f_b_valid.
- Residual (not eliminated): on entry the f_b filter holds measured history, so a short transient (about one filter time constant) remains; the lpf_f/lpf_u steady state is identical.
## Module
- in.f_b = _f_b; in.f_b_valid = !model_acc; c_prev computation removed.
- Hysteresis: _acc_stale_latched / _acc_fresh_since, leave mode (a) after 20 ms continuous fresh+finite acc; selectStageMode untouched.
- inject only if mode == Indi. Hold without held value: yaw_hold = yaw_sp if finite else yaw of _q (att_ok) else 0.
## Tests (docker)
- New: InvalidFbConvergesToModelInversionWithDelay (delay 2 and 3, 300 cycles, NaN f_b, f_b_valid=false, |t_c-(a_ref-g)|<0.05 max, <1e-3 at end), InvalidFbStepInARefIsBounded.
- IndiAccelControl 49/49 pass (was 47); ctest -R Indi 8/8 pass (IndiStageMode included).
- Break check (u_sub uses undelayed u_in): IndiAccelControlTest.cpp:396 Failure x2, `[ FAILED ] InvalidFbConvergesToModelInversionWithDelay`, 48 passed 1 failed. Reverted (u_sub back to _u_buf[i_d]).
## Build
- `make px4_sitl_default` in docker: no warnings/errors in grep, exit 0 (make's status via PIPESTATUS).
## UNVERIFIED
- make format / check_format not run; no SITL flight; entry/exit transient magnitude (f_b filter history) not quantified; no unit test for module hysteresis/inject gating/Hold yaw (module code not gtest-covered).
