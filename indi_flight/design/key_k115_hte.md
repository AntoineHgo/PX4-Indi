# Key K115: second review of 8f57b47f7e (runner hover thrust honours HTE valid flag)

Verdict: ACCEPT with 0 BLOCKING, 2 MAJOR-ish gaps in test coverage (items M1, M2), 3 MINOR. Core logic matches PX4.

## PX4 check
mc_att_control_main.cpp:237-247: valid -> clamp(hte, .05, .9); else -> MPC_THR_HOVER (unclamped). Curve (throttle_curve, CURVE=0 default branch) centres on `_hover_thrust_slew_rate.getState()` (slew 0.05/s, line 72/413), not the raw value. Runner's valid-flag condition is the right one. Param fallback is read live from the vehicle (get_param_float). Spec 1 and 2 met in code.

## Findings
- M1 (MAJOR, test gap, spec 3): run.json logging (meta["hover_thrust_valid"], ["mpc_thr_hover"], stick.hover_thr_used) has no test; mutations deleting them pass. Fix: factor meta fill into a pure helper (e.g. hover_meta(ht, valid, param) -> dict incl. hover_thr_used and hover_thr_source in {"hte","mpc_thr_hover"}) and assert on it.
- M2 (MAJOR, spec 3): no "source" field is recorded; only inferable from valid flag. hover_thr_used exists only inside meta["stick"] (run_scenario.py:898-899), so attitude/rate runs (which use thr0 for altitude feedforward, :890) do not record the used value. Fix: set meta["hover_thr_used"] and meta["hover_thr_source"] next to :886 for all runs.
- m1 (MINOR, test gap): stick_profile guard (stick_profile.py:73) has no test; removing it passes. Fix: pytest.raises-style test of thrust_to_stick("stabilized" ...) with hover 0.05 and 1.0.
- m2 (MINOR): hover_thrust_used clamps to [0.05,0.9] also on the param fallback; PX4 does not clamp the param (att_control:246). Clamp up to 0.08 then makes guard at stick_profile.py:73 raise ValueError mid-run for hover in [0.05,0.08] (valid for light quads). Either accept (fail loud) or document; fix: clamp only the HTE branch to match PX4.
- m3 (MINOR, UNVERIFIED-in-sim): PX4 centre is slew-limited (0.05/s). thr0 is sampled once at t_hold; if HTE moves after, or the slew state still lags at mode switch, centre stick differs from thr0 by up to the lag. Fix: log thr0 vs later HTE, or wait for slew settle (|dH|/0.05 s) before switching.
- Note: pytest not installed on host; ran tests via the file's __main__ runner (same assertions).

## Mutation results (each reverted, tree clean, tracked files only)
| Mutation | Result |
|---|---|
| valid flag ignored | caught |
| fallback 0.5 instead of param | caught |
| isfinite check removed | caught |
| upper clamp removed | caught |
| lower clamp removed | caught |
| valid parse "true" removed | caught |
| MPC_THR_CURVE unpinned | caught |
| MPC_MANTHR_MIN unpinned | caught |
| MPC_THR_MAX unpinned | caught |
| meta hover_thr_used removed | SURVIVED (M1) |
| meta mpc_thr_hover removed | SURVIVED (M1) |
| stick_profile guard removed | SURVIVED (m1) |
| main() wiring thr0 = ht or 0.5 | SURVIVED (wiring in main() untested; fix with helper above) |

## UNVERIFIED
px4-param show -q float output format and px4-listener "valid: True" text (regex/parse only checked against the test fixture); no sim run.

## Fix (S116, H116)
Tests: tests/test_run_scenario_hooks.py 5 -> 9 (test_stick_profile.py unchanged, 3 -> 3 pass; hooks+stick all pass). Each mutation applied once, test failed, file restored (cmp vs backup).
- M1 run.json hover fields: run_scenario.py `hover_meta()` (after hover_thrust_used, ~l.622), used by main() `meta.update(hover_meta(...))`. Test `test_hover_meta_fields_and_source`. Mutations (drop hover_thr_used, hover_thr_source, mpc_thr_hover, hover_thrust_valid): all caught.
- M2 every run records meta["hover_thr_used"] and meta["hover_thr_source"] ("hte"/"mpc_thr_hover"); meta["stick"]["hover_thr_used"] kept. Same test.
- m1 stick_profile guard: test `test_stick_profile_guard_matches_px4_range`; guard removed -> caught.
- m2 hover_thrust_used (run_scenario.py ~l.615): clamp only the valid HTE value, param fallback unclamped as PX4. Test `test_hover_thrust_fallback_not_clamped`; clamping the fallback again -> caught.
- Guard (stick_profile.py:73): now `0 < hover < THR_MAX` since PX4 accepts hover 0.05-0.08 (the curve is still monotone there); below-hover thrust with hover <= MANTHR_MIN saturates to stick 0 (unreachable, also avoids /0 at 0.08). Mutation removing that branch -> caught (assertion added to the guard test).
- main() wiring (thr0 = ht or 0.5): `test_main_wires_thr0_from_hover_meta` (source-inspection of main, not a behavioural test); mutation caught.
- m3 (slew lag) not addressed; still UNVERIFIED-in-sim. No sim run for this fix.
