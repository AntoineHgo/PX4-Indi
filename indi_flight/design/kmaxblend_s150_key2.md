# kMaxBlend 0.3 -> 0.5, independent review (key 2)

1. Arithmetic: correct. u_meas = s*u_cmd, hover needs u_meas = u_hover, so s = 2*u_hover gives u_cmd = u_hover/s = 0.5,
   gap = 0.5 - u_hover < 0.5 (u_hover > 0). 0.5 is a supremum, never reached. Past 2x-hover sag the gap can exceed 0.5, and then
   the clamp at the bound is the intended behaviour. Negative gap (s > 1) is only u_hover*(1 - 1/s), small.
2. No dependency on 0.3 found. kMaxBlend is used once (indi_accel_control.cpp:349). The only 0.3f in the module is the unrelated
   ALTITUDE_THRESHOLD (McIndiPosControl.hpp:308). Seed: reset() takes b as is (cpp:121-122). IndiPosStatus.msg:18 has no range.
   Negative side: u_f = u_meas + b (cpp:353) can only reach about u_model, which is >= thr_min*k_cmd, because b converges to
   u_model - u_meas. Even if u_f were <= 0, t_c,z > -kMinUpThrust is forced to -max(c_min, kMinUpThrust) (cpp:369-371).
   The collective is clamped to [c_min, c_max] (cpp:376-420) and thrust is constrained again (cpp:422). The invalid-telemetry
   path u_sub (cpp:334) adds b to the buffered u, so it stays bounded and consistent.
3. Test: it exercises the bound. At 0.3, b would clamp at 0.3, so EXPECT_NEAR(blend, 0.4, 0.01) and the u_cmd check (0.89) would fail.
   Fixture limits are thr_max 1.0 (Test.cpp:56), u_meas about 0.49 (< 0.98), so neither clamp nor saturation freeze interferes.
   Last assertion (Test.cpp:851) is redundant with the blend check (algebraically u_cmd - gap + b = u_cmd iff b = gap), not vacuous.
   The blend_frozen check is not vacuous. A negative-side test (b about -0.4) is absent.

VERDICT: MINOR (a) no negative-side bound test (suggest gap -0.4 / scale > 1); (b) Test.cpp:851 assertion redundant;
(c) hpp:85-86 comment says "<= 0.5" while the real bound is < 0.5 (harmless).
