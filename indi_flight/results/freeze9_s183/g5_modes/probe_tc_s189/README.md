# probe_tc_s189 (F4 kSetpointLeadTc 0.03 -> 0.01)
Built: make px4_sitl_default in docker with kSetpointLeadTc=0.01; build.log shows indi_rate_control.cpp.o, McIndiRateControl, px4 relinked (21/21).

## Result: seed 3 (mode_switch10, exact freeze-9 command/params, posctl), tc=0.01
Verdict: FAIL (same as f9). Seed 1 not flown (rule: only if seed 3 passes).
Edge tilt_err deg (limit 5): probe tc01 / f9 / f6
 2>1   0.50 / 0.30 / 0.47
 1>2   2.32 / 10.66 / 2.40
 2>15  0.55 / 0.57 / 0.53
 15>2  1.25 / 6.20 / 3.30
 2>4   5.89 / 6.05 / 2.44   <- fails
 4>2   5.08 / 4.26 / 2.64   <- fails
 2>1   0.57 / 0.29 / 0.48
 1>15  0.07 / 0.05 / 0.04
 15>4  5.49 / 5.51 / 4.15   <- fails
 4>2   4.85 / 5.63 / 2.76   <- fails
Hold-edge errors (posctl<->hold) are unchanged by tc 0.03->0.01, so F4 is NOT the cause of the hold-edge lag.
Caveat: 1>2 and 15>2 edges changed (10.66 -> 2.32, 6.20 -> 1.25): either run-to-run variance (single seed, f9 1>2 10.66 looks like an outlier) or a tc effect; not resolved with one flight.
## Restore
Header restored with git checkout; git status --short src/ empty; SITL rebuilt at freeze-9 (rebuild_f9.log, 299/299 steps, indi_rate_control.cpp.o recompiled): yes.
