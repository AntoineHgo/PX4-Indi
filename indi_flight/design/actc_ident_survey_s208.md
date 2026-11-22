# S208 survey: ACT_TC identification (Q27 owner item 1). Read-only; no flights, no edits elsewhere.

## 1. What exists
- Concept only: design/ident_concept.md:12 and :28 (M2 = per-motor fit of omega^2 vs motor command, first order with
  separate up/down tau plus dead time, plus W_MAX and thrust-curve map). DECISIONS.md:626 D-IDENT repeats it ("actuator
  fit for ACT_TC/W_MAX/thrust curve"); D-IDENT-J (:643) and D-IDENT-STOP (:657, freezes estimator work) say nothing more.
  Only three D-IDENT* entries exist. Acceptance conditions (i)-(v) at :632-639 (start independence, F, mismatch self-test).
- NOT implemented as an estimator: no M2 code in bench/ident_fit.py, ident_iv.py, rate_fit.py, ident_fit_yaw.py (those fit
  G1 and G2_Y only, IV on gyro vs actuator_torque_measured: ident_fit.py:230, ident_iv.py:246). No self-test, no key.
  ident_iv.py:209 has the lag correlation for ERPM_DLY (M3), the only telemetry-latency estimator.
- Closest tool: bench/a51_motor_latency.py (analysis script, no test, no key). Per motor fits rpm = a + b LP1_tau(cmd(t-d)),
  grid d 0-30 ms, tau 15-60 ms, from esc_status vs actuator_motors, single symmetric tau. Result in
  results/g2_freeze_s160/xcheck_rate_a51.md:7-10: free fit tau 41-45 ms (nominal 33 ms), d 1.6-3.6 ms. The log tau is
  biased high versus plant tau, so a bias must be measured first. ACT_TC runs so far are only gain comparisons:
  results/act_tc_s128 (0.05 vs 0.033), results/a37_actlag_s103 (delay line check), results/q26_actc_s207 (re-fly).
- Keys: key_k120_ident_iv.md, key_k124_ident_fit.md, key_k125..., key_k126/key2_ident_fit_yaw_s204.md: none for ACT_TC.
- Folders results/ident_m3a_s123, ident_yaw_*: G1/G2_Y, within 0.8 % (roll/pitch) of derived. Nothing on ACT_TC accuracy.

## 2. Data
- Manoeuvre: firmware multisine injector on the INDI torque setpoint, one axis at a time (roll/pitch/yaw), MC_INDI_INJ_AX,
  _AMP (0.02 norm torque, max 0.2), _FMIN/_FMAX (max 200 Hz, default 60), _NP, _TP, _DLY, _PT, _RAMP
  (src/modules/mc_indi_rate_control/mc_indi_rate_control_params.yaml:258-355; IndiInjection.cpp). No PINJ params exist. The
  injection is a torque command, so per-motor commands (actuator_motors) carry it through the allocator: usable for M2.
  Roll/pitch torque injection excites motor pairs in antiphase (identifiable up and down), yaw in two pairs. Amplitude
  +-0.02 torque is small versus tau asymmetry visibility: check that spin-up and spin-down both occur (needs amp > 0).
- Topics (bench/run_scenario.py:73-90 LOG_TOPICS, SDLOG_PROFILE 17, interval 0 = every update): actuator_motors (command),
  esc_status (esc_rpm, via eRPM telemetry model; src/modules/logger/logged_topics.cpp:72 default 100 Hz, overridden to full
  rate), actuator_torque_measured, indi_rate_status, sensor_gyro 800 Hz. esc_status updates once per ESC output frame
  (800 Hz default sim, 400 Hz variant; GZMixingInterfaceESC.cpp:245-263), so >= 200 Hz is met in the bench. Real flights
  use default logging (esc_status 100 Hz): flag for the product claim, not for the SITL bound.
- Runner scenario names: indi_m3a, hover_long (results/a37_actlag_s103/fly.sh).

## 3. G3 plant variants
- bench/g3_sample.py:30-34,174-190: tau_up, tau_down (slow side = drawn tau in [0.5, 3] x nominal, fast side = slow/asym,
  asym log-uniform [1,3], 10 % inverted, floor 0.5); loop delay 0-10 ms in 1.25 ms steps; TEL_LAT 0-3 frames.
- bench/g3_run.py:115-145: tau via --model-variant tau/tau_up/tau_down; delay via --dly-act/--dly-imu (integer ms, rounded,
  g3_run.py:129-139); telemetry via param SIM_GZ_ERPM_LAT (1 frame = one ESC output period, 1.25 ms at 800 Hz).
  run_scenario.py:880 --model-variant accepts fixed factors. So a fixed-factor sweep is possible with existing hooks:
  g3_run takes a factor file, or call run_scenario directly with these flags. No firmware change.
- Not found: controller-side ACT_TC draw (Q27 says tooling still to do for the later G3 re-fly); not needed for this sweep.

## 4. Plan (<= 12 bullets)
- Write bench/ident_actc.py reusing ident_iv.py filtering/lag helpers and a51's LP1 model: per motor fit
  omega^2 (esc_rpm^2/W_MAX^2) to command with separate tau_up/tau_down (two-regime fit: regress d(omega2)/dt on cmd-omega2
  split by sign of the increment), delay d free, intercept; saturation excluded as ident_fit.py does.
- Report both tau_up and tau_down plus tau_slow = max and tau_mean = average; the firmware needs one number, so the bench
  decides which. State per run which one the fit tracks.
- Synthetic self-test (bench/tests/test_ident_actc.py): known tau_up/tau_down (asym 1, 3, inverted), delay 0-10 ms, telemetry
  0-3 frames, noise; closed-loop case (torque loop around the actuator, injected multisine), OLS-bias comparison, a
  deliberate delay mismatch that must fail (D-IDENT iii lesson), weak instrument gate. Fix delay-vs-tau confounding by
  joint grid (delay and tau are correlated: a51 saw tau 41-45 vs 33 nominal, so quantify that bias on synthetics first).
- Second key (lesson 17): independent re-implementation by a separate reviewer, mutation list like key_k124.
- SITL sweep, injection with MC_INDI_INJ_AX roll then pitch in one flight (ID_OK 0 config), params only. Proposed design:
  tau_slow {0.5, 1, 2, 3} x asym {1, 3 down-slow, 3 up-slow} x (delay, frames) {(0,0),(10,3)} = 24 flights, seed 1;
  plus the 4 corner-of-interest repeats at seed 2 (noise) = 28. Smaller screen: tau {0.5,1,3} x asym {1,3 down-slow}
  x {(0,0),(10,3)} = 12, then fill the failing region. Marginal (delay-only, frames-only) cells (0,3) and (10,0) at
  tau 1, asym 3: +2. Estimate about 15 min CPU/flight at speed 4 (g3 tooling).
- Output: table of est/truth for tau_up, tau_down, tau_slow, tau_mean per cell; bound = worst-case one-sided ratio
  ACT_TC_est / tau_slow_true (and the same for mean) over the grid, with max and 95 % of cells. This becomes the box
  U[lo, hi] of the controller ACT_TC draw in GATES.md (Q27 item 1); the rule is then capped/two-sided per item 2.
- Firmware: none expected (injector and logged topics exist). Only possible need: fixed esc_status logging rate in real
  flights, and ID write-back of ACT_TC (MC_INDI_ID_OK path); ask the owner first.
