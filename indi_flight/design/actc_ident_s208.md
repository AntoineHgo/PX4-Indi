# ACT_TC identification step and its error measurement (S208, Q27 item 1, D-ACTC-IDENT)

Purpose: give `MC_INDI_ACT_TC` an identified value and a measured error bound; the bound defines the G3 controller
ACT_TC box (GATES "Owner amendments S208"). Survey of what exists: `design/actc_ident_survey_s208.md`.

## Estimator (`bench/ident_actc.py`, new; the concept M2 of `design/ident_concept.md`, never implemented)
- Data: per motor, command `actuator_motors.control[i]` and measured rotor speed `esc_status.esc[i].esc_rpm`, both
  logged at every update (~800 Hz in the bench), on the hover + multisine manoeuvre the firmware injector already
  flies (`MC_INDI_INJ_*`, roll then pitch). Saturated samples (command at 0 or 1) excluded.
- Signal: y = (rpm / rpm_max)^2, the firmware's actuator state variable (u = omega^2 normalised).
- Model: output error. y_hat = a + b x, x = asymmetric first-order lag of the command delayed by d samples, using
  tau_up while the delayed command is above x and tau_down otherwise. (a, b) by linear least squares given x;
  (d, tau_up, tau_down) by grid search then local refinement on the residual sum of squares. A symmetric fit
  (tau_up = tau_down = tau_sym) is reported alongside: tau_sym is the single number the firmware can take.
- Why output error and not regression on d(y)/dt: the derivative of a quantised, noisy eRPM signal biases an
  equation-error fit, and INDI feeds the measured rotor speed back into the command (closed loop). Output error
  simulates x from the command only, so white measurement noise on y does not bias it; the self-test checks this.
- Delay d absorbs actuator-path delay and telemetry frames jointly; it is reported, not used for the box. The a51
  script (symmetric tau, free delay grid) read 41-45 ms against 33 ms nominal: the self-test must show the new
  estimator has no such bias, or measure it.
- Fit-quality check: normalised residual RMS and the condition of the (tau_up, tau_down, d) minimum (curvature); a
  failed check is a failed identification, never a value. Output: per motor and median over motors of tau_up,
  tau_down, tau_sym, d, check flags; JSON plus one table line.

## Self-test (`bench/tests/test_ident_actc.py`), before any SITL use
Synthetic plant with known tau_up/tau_down (asym 1, 3, inverted 1/3), delay 0-10 ms, telemetry 0-3 frames of 1.25 ms,
eRPM quantisation and noise, multisine command; a closed-loop case (command = multisine minus a gain times the noisy
measured y). Pass: noise-free within 2 % per tau and d within one sample; noisy and closed-loop within 10 %; a
deliberate mismatch (fit with d forced 10 ms off) fails the quality check; a command without excitation fails.
Second key (lesson 17): an agent that has not seen this note's reasoning reviews the code against this page.

## SITL error measurement (GATES G6 "6c")
Grid on quad5in, ID_OK 0 configuration, params-only, existing g3_run/run_scenario hooks (`--model-variant`
tau_up/tau_down, `--dly-act`, `SIM_GZ_ERPM_LAT`): tau_slow {0.5, 1, 2, 3} x 0.033 s; asymmetry {1, 3 down-slow,
3 up-slow}; (delay ms, frames) {(0, 0), (10, 3)} = 24 flights, seed 1; seed 2 on the 4 tau corners of asym 3
down-slow; marginals (0, 3) and (10, 0) at tau 1, asym 3 = 30 flights. Pre-test: 2 flights (tau 1 asym 1; tau 3 asym 3,
(10, 3)). Output: est/true table per cell for tau_up, tau_down, tau_sym; ratios tau_sym_hat / tau_slow and
tau_sym_hat / tau_mean, min / max / 95 %. That table, the ACT_TC rule (capped or two-sided, from the bound and the
delay, model margins on box corners) and the proposed box go to the owner as Q28. No G3 flight before the answer.
