# T123 second-key review (S60): code vs outer_loop_candidates_r2 A2, A3, A5, A6, A7 and r4 A13-A14

Status: complete. Verdict at the end of this file. Read-only review; the only file written is this one.

## PositionControl side (src/modules/mc_indi_pos_control/McIndiPosControl.cpp)

- A2 AGREE on ht ordering: `ht = (flying && _hte_valid) ? _hte : MPC_THR_HOVER` (:655), `setHoverThrust(ht)` once per cycle (:656). `updateHoverThrust` not called in this file (grep). Note :433 also calls `setHoverThrust` in the parameter-constraint path; it is overwritten by :656 before every `update()`, so harmless.
- A2 AGREE on `resetIntegral()` every cycle: :670 (idle branch), :742 (active branch), :773 (else branch), :800 (after update).
- A2 AGREE on G: `G = kGravity / max(ht, 0.05)` and `setThrustModel(G, 1.f)` (about :145-146 of runIndiStage).
- A2 AGREE on T_meas scale: the active path passes `in.mean_u` from ESC (u = (omega/omega_max)^2, :108-134). The bypass path seeds the lib with the published collective `c` (:203-214). These are consistent only if the rate-stack thrust setpoint is the same u-scale; this is the O-6 assumption, not verified in code.
- A3 AGREE on gating: `want_indi = armed && (pos || vel) && FLIGHT && !flying_but_ground_contact` (:780-783). RAMPUP is excluded by the FLIGHT check.
- A3 PARTIAL on fallback wording: bypass uses `coll = fresh_thr ? _coll_meas : coll_stock` (:205). When the thrust setpoint is stale, the code uses the stock thrust published this cycle, not "the module's own last published thrust" as the spec states. `_last_thrust` is only the fallback when `coll_stock` is non-finite (:205, :208). Behaviour is arguably better (it matches what is actually published), but it does not match the written spec.
- A3 AGREE on stock publication in bypass: `att_sp` is only overwritten in the active branch (`thrustToAttitude`, :191), so bypass publishes the stock setpoint.
- A5 AGREE: `kMaxAge = 20_ms` for attitude, acceleration and thrust setpoint (:79, :168-171). Any stale attitude or acceleration makes `can_run` false, which goes to bypass (:178-179, :203).
  - Gap: ESC uses `kEscMaxAge = 100_ms` and only clears `in.mean_u_valid`. It does not bypass. The spec's R33 rule ("every new input has a staleness rule and a fallback") is met for ESC, but the spec does not state the ESC threshold. Confirm it is intended.
- A6 AGREE: `_indi.setFeedforward(false); // A6` (:56).
- A7 AGREE: `local_pos_sp.thrust[0..2] = thr_vec` (:194-196) with `thr_vec = out.t_c / G` (NED). `local_pos_sp.acceleration` is the input a_ref (:162) and is not overwritten here.
- Scale check: `thr_vec = t_c / G`, with G = g/ht. Since t_c = G * (thrust vector), the norm of thr_vec is collective in u-scale. Consistent with A2.
- A14 PC side: the stock PositionControl produces `a_ref` with NaN axes handled by the stock code. The stage gate (`a_ref.isAllFinite()`, :175) requires all three axes finite, so a NaN axis drops to bypass. That is the stock behaviour, but it is stricter than the spec's "finite a_ref on the INDI group(s)". The spec's "NaN p/v on an open group no longer drops the stage" is not satisfied at this gate if the open group produces a NaN a_ref. Verify what PositionControl emits on open axes (A15 territory).

## Bugs found so far

1. Filter re-configured while active, no reset (BUG, likely). `runIndiStage` sets `_indi_active = false` after `setFilter` with the comment "force a reset below" (:146-149). The reset only happens in the bypass path. If `can_run` is true on that cycle, the active update runs with the filter states from the old rate, with no reset. Confirm in the lib that `set_cutoff_frequency` keeps its state.
2. `in.a_ref` NaN handling (spec mismatch, not a crash). The lib zeroes a NaN axis (`a_ref(i) = a_valid[i] ? ... : 0`). The caller prevents NaN from reaching it. That is safe, but the lib gate does not check `a_ref` finiteness as A14 requires.

## Lib side (src/lib/indi_accel_control/indi_accel_control.cpp)

- A13/A14 `accel_only` AGREE: p/v finiteness skipped (:200), `p_term` and `v_ff` zeroed (:221-222), `a_c = a_ref` with no velocity term (:257). Caveat: the lib gate does not check `a_ref` finiteness; a NaN axis is silently zeroed (:218-224). The caller enforces `a_ref.isAllFinite()` (McIndiPosControl.cpp:175), so the caller path is safe, but the A14 "validity needs finite a_ref" lives in the caller, not the lib.
- A6 AGREE in effect: `setFeedforward(false)` sets `_jerk_ff = false` (hpp:144); the rate feedforward `omega_ff` is only computed under `_jerk_ff` (cpp:332-337), so it is zero. The jerk path (`_j_diff`, `_j_diff_f`, :237) still runs but is dead code on this interface. Not a bug, but worth noting that the new `_lpf_j` work is unused here.
- `_j_diff_f` is zero-initialised (hpp:204 `{}`), so there is no NaN before the first `updateJerkDifference`.
- `reset()` is not called while active: `runIndiStage` returns at the active branch before the reset (McIndiPosControl.cpp:191-199 vs :203-210). AGREE with A13 "no reset at e7".
- Filter re-configure (BUG, confirmed, minor): `setFilter` (cpp:77-81) changes cutoff and sample rate on `_lpf_f`, `_lpf_u`, `_lpf_j` without touching their states. The caller sets `_indi_active = false` with the comment "force a reset below" (McIndiPosControl.cpp:146-149), but the reset only happens in the bypass path. If `can_run` is true on that same cycle, the active update runs on filter states computed at the old rate. The effect is a transient, not a NaN. The fix is to call `_indi.reset(...)` on the re-configure edge, or to drop the misleading comment.
- No NaN propagation found: the lib returns false on non-finite inputs (cpp:200-203), and the caller falls to bypass, which resets the lib with finite values (`fresh_acc ? _f_b : (0,0,-c*G)`, `c` finite via :206). `_last_thrust` is guarded by `PX4_ISFINITE` (:208).

## Verdict

- A2 AGREE (one ht per cycle, updateHoverThrust unused, resetIntegral every cycle, G = g/ht, T_meas on the u-scale as O-6 assumes).
- A3 AGREE on gating and bypass publication; PARTIAL on fallback wording (stale thrust setpoint falls back to the stock thrust of this cycle, not the module's last published thrust).
- A5 AGREE on 20 ms attitude/acceleration bypass; ESC threshold (100 ms) is not in the spec and only drops `mean_u_valid`.
- A6 AGREE (feedforward off, omega_ff = 0).
- A7 AGREE (`thrust` = `t_c / G`, `acceleration` = a_ref).
- A13/A14 AGREE on the lib skip and no-reset-while-active; PARTIAL on where the a_ref finiteness gate lives (caller, not lib). The PC gate also requires all three a_ref axes finite (McIndiPosControl.cpp:175), which is stricter than A14's "finite a_ref on the INDI group(s)" and will drop to bypass if an open axis yields NaN.
- Bugs: (1) filter re-configured while active without reset (above); (2) the ESC staleness threshold is undocumented in the spec.
