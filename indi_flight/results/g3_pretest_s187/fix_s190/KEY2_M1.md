# KEY2 review of 4afa7a97b6 (M1 native filter re-seed)

Static review only (no build, no test run).

## Code-to-spec
- Early returns (indi_accel_control.cpp:293, 303, 310) leave all state untouched. They are before the edge line (389), so `_prev_f_b_valid` is neither updated nor stale. The edge is seen on the next accepted cycle. OK.
- Late returns (432, 511) are after the edge line. The re-seed and `_prev_f_b_valid` are consumed together, so no edge is lost or repeated. OK.
- `_last_f_b` on the edge cycle is the previous cycle's `f_bf`. That is the modelled filtered value from the gap, since `_last_f_b = f_bf` is set at line 406 on every cycle. This matches the spec.
- The re-seed sets `_lpf_f_native` and `_native_f`, so `f_bf` equals `_last_f_b`. There is no step, and later `sampleSpecificForce()` calls converge at the native bandwidth. A native sample fed just before the edge update is discarded for that one cycle (harmless).
- Other cases are unchanged:
  - valid->valid, invalid->invalid and valid->invalid: the condition is false.
  - Never-fed native filter: the `_native_fed` guard skips the re-seed. The first sample still seeds the filter via `sampleSpecificForce()`.
  - `reset()` (line 166) sets `_prev_f_b_valid = true`, so there is no spurious edge right after a reset. An invalid first cycle followed by a valid one still re-seeds. OK.
- `setFilter()` does not touch the flag and is not affected.
- No hold/bypass path between the edge line and `_last_f_b` assignment is affected.

## Tests
- `NativeRateFilterInvalidToValidHasNoStep` (IndiAccelControlTest.cpp ~1583-1630) feeds no native samples during the gap, as in the realistic case. Without the re-seed, `_native_f` would be held at 0.5. The edge output would then be about 0.5 against a_gap near 0, so the 0.05 bound fails. The test does detect the missing fix.
- The gap settle check `a_gap < 0.05` is loose. It relies on 10 cycles of about 7 tau, which is adequate.

## Findings
- BLOCKING: none.
- MAJOR: none.
- MINOR (test, ~1576): the tightened valid->invalid assertion `NEAR(a_f(0), 0.5, 0.05)` has little margin. The stage 2-pole filter with a reset at 0.5, fed the modelled value 0 once, gives about 0.5*(1-b0), with b0 about 0.082 at fc 10 Hz and fs 89 Hz. That is about 0.459, so the deviation is about 0.041 against a 0.05 bound. It passes, but a small change to the filter or the rate could flip it. A step to 0 would be detected clearly. Consider a bound of 0.06 or an explanatory comment.
- MINOR: `a_f(1) < 0.05` in the same test is trivially true (the y component is 0 throughout) and adds no step detection.

KEY2 VERDICT: PASS
