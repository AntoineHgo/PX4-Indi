# Second key: code vs spec (brief_accbreak_s84, Specification 1-5), commits 20b1c9c48b, 292b71c333

1. Idle / off identity: AGREE. inject_output needs PT==1 and axis>=0; with AX=0 or PT=0 a_ref = c + inject, t_c_applied = t_c,
   setAppliedThrust not called, thr_vec = t_c/G as before. With PT=1 and the injector idle (before DLY, after window,
   landed, disarmed) inject == 0 so a_ref = c, setAppliedThrust is gated on |d|>0, t_c_applied = t_c. No behaviour change.
   Inside the window, samples where d is exactly 0 skip the call; update() already stored the clamp of |t_c|, which equals
   the applied value then, so it is consistent.
2. PT=1 path: a_ref = c exactly; u_o = out.t_c + d goes to thrustToAttitude and local_pos_sp.thrust (thr_vec = t_c_applied/G).
   setAppliedThrust: constrain(|u_o|/(_g_t*_k_cmd), thr_min, thr_max) is the same expression as update() line 366 (m/s^2 in,
   _g_t = G, _k_cmd, same limits), applied after update() so it overrides _thrust_prev (line 390). Non-finite ignored.
   Library left slightly inconsistent (minor): jerk difference uses a_ref = c (right for an output-point break); omega_ff and
   logged q_d come from the library t_c, not u_o (small d, negligible); _coll_clamped reflects t_c, not u_o, so the blend
   anti-windup does not see a clamp caused by d.
   Bypass of tilt/collective clamps: with small finite d, no NaN (t_c checked finite, d finite) and no inversion (t_c_z <=
   -kMinUpThrust); a d larger than the vertical thrust on z could invert the vector. Bench only, AMP bounded, stock
   attitude/rate loops saturate downstream. Not verified: thrustToAttitude behaviour for huge d.
3. Logging/csv: t_c and t_c_applied give c_o and u_o unambiguously at full rate (difference = d). pinj_csv --point output uses
   x = u = t_c_applied, y = c = t_c, same column order/sign as the input path (x = a_c = u, y = a_c_pre_inject = c), so
   L = -G_yd/G_xd is identical. Self-test run: all PASS. Swapped copy in /tmp (x,y exchanged in the output branch):
   test_output_point_columns FAILS (est PM -43.37 vs truth 43.37). Caveat: the test mocks pyulog and builds the fields from the
   simulated loop, so it checks the column mapping, not the firmware signs.
4. Unit test AppliedThrustSetsModelPath asserts -t_f(2) == c_applied (0.9 g) with invalid telemetry; with a no-op method the
   model path would follow the previous out.thrust (a_ref -2 puts that near g+2), so it would fail by several m/s^2. Real
   assertion. The NaN part only shows non-finite is ignored; the clamp branch is not exercised (minor gap). Not built/run by me.
5. Yaml: default 0, enum, bench-only wording, MC_INDI_PINJ_ prefix consistent with siblings. Minor vs
   parameters.instructions.md lines 19-20: long re-lists the options ("0 adds... 1 adds..."), which the guideline forbids
   (put detail in option labels or "Label: effect." lines). Same style as AX, low priority.

Verdict: AGREE WITH MINOR
Blocking items: none.
Minor: (a) yaml long wording; (b) _coll_clamped / omega_ff / logged q_d not derived from u_o; (c) unit test does not
exercise the clamp; (d) csv test checks column mapping only.
