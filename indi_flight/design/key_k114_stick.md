# K114 second key: stick_profile (commit 807fd6a08a) against PX4 source

Verdict: the stabilized and acro maps and their inverse are correct against the source at default params. No BLOCKING. One MAJOR (hover value fed to the curve is not always the one PX4 uses), three MINOR.

## Verified correct
- Receiver: src/modules/mavlink/mavlink_receiver.cpp:2476 throttle = z/500 - 1 (z in [0,1000]). No other rescale found in src/modules/manual_control (ManualControl.cpp only forces -1 on invalid/zeroing at :129-137). stick_profile.py:24-31 matches.
- Stabilized: mc_att_control_main.cpp:209 thrust_body[2] = -throttle_curve(_manual_control_setpoint.throttle). The stick is passed raw (no expo, no deadzone, no scaling). Default branch (MPC_THR_CURVE 0, yaml multicopter_stabilized_mode_params.yaml:52) is interpolateNXY {-1,0,1} -> {_manual_throttle_minimum, _hover_thrust_slew_rate, MPC_THR_MAX} (:134-137). Defaults MANTHR_MIN 0.08 (yaml :34), THR_MAX 1.0 (limits yaml:91). stick_profile.py:73-76 and 84 match both branches.
- _manual_throttle_maximum (:141, ramps to 1 at 0.5/s once spooled up, forced 0 if not spooled up, :405-409) caps nothing in flight at defaults.
- _manual_throttle_minimum ramps 0 -> 0.08 at 0.05/s only when not landed (:397-402); in air it equals 0.08.
- Acro: mc_rate_control/MulticopterRateControl.cpp:171 and mc_indi_rate_control/McIndiRateControl.cpp:354 both thr = (throttle+1)/2, so stick = 2 thr - 1. Matches :70-71. No hover dependence.
- Inverse: both branches algebraically invert the forward map; clipping in stick_to_raw (:26) clips to [-1,1] before rounding, so thr < MANTHR_MIN or > THR_MAX saturates at the curve ends (correct, PX4 cannot exceed them either).

## MAJOR
1. run_scenario.py:860-862 thr0 is the raw hover_thrust field of the last HTE message, without checking `valid`. mc_att_control_main.cpp:237-247 uses the HTE value only if valid, clamped to [0.05, 0.9]; if valid is false it uses MPC_THR_HOVER (slewed). The estimator publishes hover_thrust with valid=false while converging (MulticopterHoverThrustEstimator.cpp:226-238), so the runner can use a finite non-valid estimate that PX4 ignores. Also the fallback thr0 = 0.5 (run_scenario.py:862) is wrong for the quad5in airframe: PX4's fallback is MPC_THR_HOVER = 0.137 (ROMFS/px4fmu_common/init.d-posix/airframes/4040_gz_quad5in:56). A NaN message (invalid-publish, :249) hits this fallback. Effect: centre stick is off hover by up to ~0.36 thrust, the same class of fault as S113. Fix: parse `valid:` and, if not valid, use the MPC_THR_HOVER read via param; clamp to [0.05, 0.9] as PX4 does. The runner's 0.1 lower bound also differs from PX4's 0.05.

## MINOR
2. _hover_thrust_slew_rate (initial 0.5, 0.05/s, :72, update :412-414 in every cycle with attitude control) is not the HTE value but a slewed copy. If thr0 is read at t_hold while the slew has not converged (start 0.5 -> 0.137 takes ~7 s) or the HTE drifts later in the run, the applied thrust differs by (state - thr0) * gain. Impact is small once hover has been long enough (read happens after T_HOLD_S), but the log never records PX4's actual slew state. Suggest checking T_HOLD_S > 10 s of valid HTE or reading the slew indirectly (centre-stick thrust in the attitude setpoint log).
3. Constants depend on defaults: MANTHR_MIN/THR_MAX/MPC_THR_CURVE are hard-coded (stick_profile.py:20-21) and not in STICK_PARAMS (run_scenario.py:94-95). 4040_gz_quad5in sets none of them, so defaults hold, but another airframe (e.g. 4020_holybro_px4vision_v1_5:60 sets MANTHR_MIN 0; 4601 sets THR_MAX 0.5) would silently break the inverse. Pin them in STICK_PARAMS or assert the airframe.
4. thrust_to_stick divides by (hover - MANTHR_MIN) and (THR_MAX - hover) with no guard (stick_profile.py:74-75); fine for hover in (0.1, 0.9) but hover <= 0.08 gives a division by zero or sign flip. Unreachable through the runner window; add an assert.

## Tests (bench/tests/test_stick_profile.py)
- test_stabilized_round_trip (:47-56) uses an independent copy of the curve, hover 0.137, and samples with both positive and negative vz_up (sin(2t) at t=2.5 is negative), so a wrong inverse in either branch (e.g. swapped denominators, slopes 0.863 vs 0.057) would fail; tolerance 0.003 equals about 1.5 raw steps. Would catch a wrong inverse: yes.
- Not covered: saturation at curve ends for stabilized (only altctl clip tested, :31-33), hover outside the runner window, and the runner's HTE-validity logic (finding 1). The test's curve copy shares the same hard-coded 0.08 / 1.0 as the module, so it cannot detect a default change in PX4.
- Acro test (:36-37) re-states the formula rather than an independent PX4 copy; weak but correct.
