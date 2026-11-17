# D-GAP review r2 (closure check of the S71 amendment against dgap_review_r1.md)

| item | answered | note |
|---|---|---|
| 1 b edge semantics (freeze not snap; ground, A3/A8 bypass, e7; reset() leaves b; invalid -> freeze with coll_f = model; clamp freeze; bound in u units) | yes | All listed edges are stated. Two small gaps. (a) Recovery is implicit: it should say coll_f = meas + b_frozen on telemetry recovery. (b) The "allocator collective-saturation flag" may not exist. If only the module clamp is available, downstream saturation (weak motor at 100 %) still winds b. Say which signal is used, or that the flag is added. |
| 2 coll_model = previous clamped command, second delay/LPF path, b in u units and logged | yes | Matches r1. Logging b also covers the unit-mismatch check. |
| 3 overturn criterion, tb window, phase-cost bound | yes (wording) | Asin bound, HF-mode test at tb and tb/3, PM >= 45 deg and window 0.3-2.5 s are all present, and the criterion can now fire. Wording: "for every tb in the window" is ambiguous. State that (d) is reverted only if no tb in the window passes. Also say what the 3 dB peak is relative to (|A| vs 1). |
| 4 VEL_I_ACC stay 0; (d) runs in acceleration-only groups | yes | Also states b freezes across e7 (item 1). |
| 5 tests and flight check | partial | See below. |
| Q3 BLOCKING (edge semantics, snap vs A16, saturation windup) | yes | Snap is explicitly not copied. Freeze rules agree with r1 and no freeze rule winds up. Airborne bypass freezes, where r1 allowed either, so it is acceptable. First takeoff starts from b = 0 and has one tb-long sag. Acceptable, but note it. |

Item 5 detail:
- The unit test names no numeric tolerance. r1 asked for |e_z| < 1 mm after 5 tb and e_z = 0.15 g/(Kp Kv) +-2 % at tb = 0. "Steady collective error" is a different quantity from the standing z error that the flight metric scores.
- Missing cases: reset() keeps b, 50 invalid cycles then recovery with |dT| < 1e-3 (no sag), and T at thr_max leaves b unchanged. Without them the clamp and recovery freezes can be broken and the stated tests still pass. The e7 edge is also untested.
- The flight check has no pass criterion for the land/re-takeoff (no tb-long sag, e.g. z dip bound). "b held" is not measurable from the flight metric alone unless the logged b is compared across the ground phase.
- The hover pretest gate is not repeated.

R2: OPEN. Items left: 5 (numeric unit-test thresholds, missing freeze, recovery and reset tests, re-takeoff pass criterion). Minor wording only: 3 (revert rule), 1 (recovery rule, saturation signal).
