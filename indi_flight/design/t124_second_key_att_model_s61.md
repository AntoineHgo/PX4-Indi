# T124 second-key linear model prediction: attitude step (S61)

Script: indi_flight/bench/t124_att_step_key.py (fixed-step explicit Euler, dt = 1/800 s, delay = integer steps: 8 and 16).
Derived independently from the stated equations only.

## Model
- tau_a * da/dt = nu(t - d) - a, tau_a = 0.033 s
- d(omega)/dt = a, d(theta)/dt = omega
- nu = K(r - omega) - K tau_c a + kff * rdot_f, K = 20 rad/s, tau_c = 0.05 s
- rdot_f = (r - rf)/tau_f, rf = low-pass of r, tau_f = 0.01 s
- r = P(theta_sp - theta), P = 8, theta_sp = 15 deg step at t = 0

## Results (step response, dt = 1/800 s)

| d [s] | kff | OS [%] | t_peak [s] | peak [deg] | 2% settling [s] |
|-------|-----|--------|------------|------------|-----------------|
| 0.010 | 0 (kff=0)     | 16.11 | 0.384 | 17.42 | 0.820 |
| 0.010 | 1 (K tau_c)   | 1.22  | 0.421 | 15.18 | 0.294 |
| 0.010 | 2 (1+K tau_c) | 0.00  | none (monotonic) | 15.00 | 0.532 |
| 0.020 | 0 (kff=0)     | 17.22 | 0.372 | 17.58 | 0.806 |
| 0.020 | 1 (K tau_c)   | 0.75  | 0.416 | 15.11 | 0.288 |
| 0.020 | 2 (1+K tau_c) | 0.00  | none (monotonic) | 15.00 | 0.539 |

Settling time = time of last sample with |theta - 15 deg| > 0.3 deg, measured from the step. No case was unsettled at T = 3 s.

Convergence check (dt = 1/3200): OS = 15.81 / 1.18 / 0 % (d = 10 ms) and 16.87 / 0.73 / 0 % (d = 20 ms); settling 0.818 / 0.296 / 0.535 s and 0.805 / 0.290 / 0.541 s. So the overshoot figures are uncertain by about +-0.5 percentage points and settling by about +-0.01 s, both from the Euler step.

## Rate-loop poles (kff = 0, P = 0, d = 0)
Characteristic equation: tau_a s^2 + (1 + K tau_c) s + K = 0, i.e. s^2 + 60.61 s + 606.06 = 0.
Roots: s = -12.63 1/s and s = -47.97 1/s.
Dominant time constant: 1/12.63 = 0.0792 s.

## Analytic result (d = 0, tau_c = tau_a, kff = K tau_a)
Note: this is not one of the table cases (there tau_c = 0.05 s, not tau_a). It is the case where the feedforward cancels the actuator-related term.

Let G = s/(tau_f s + 1) be the rdot_f filter. Laplace of the loop with a = s*omega:
(tau_a s + 1 + K tau_a) s omega + K omega = K r (1 + tau_a G)
so
omega/r = K ((tau_a + tau_f) s + 1) / [ (tau_f s + 1)(tau_a s + 1)(s + K) ].

The factorisation used is tau_a s^2 + (1 + K tau_a) s + K = (tau_a s + 1)(s + K).

- Limit tau_f -> 0: omega/r = K/(s + K). The (tau_a s + 1) factor cancels exactly. The closed loop is first order with time constant 1/K = 0.05 s and DC gain 1.
- With tau_f = 0.01 s: zero at -23.26 1/s; poles at -100, -30.30, -20.0 1/s; DC gain 1.

Check: the RK4 solution of this transfer function's canonical realization matches the Euler sim to 1.7e-3 rad/s at dt = 1/3200 and 4.3e-4 rad/s at dt = 1/12800 (error scales as dt).

## Uncertainties
- The attitude-loop OS and settling use the Euler step; the overshoot numbers are not converged to better than about 0.5 pp (see convergence check above).
- Overshoot for kff = 0 is the dominant result: about 16-17 %, versus about 1 % at kff = K tau_c and 0 % at kff = 1 + K tau_c.
- The rdot_f term is read as the derivative of the filtered r (equivalently the filtered derivative of r; these are identical in LTI form).
- The analytic closed form was derived only for d = 0, tau_c = tau_a. The table cases use tau_c = 0.05 s, so the pole-zero cancellation does not apply to them.
- The kff = 1 + K tau_c case is monotonic (peak at the window end, no overshoot); its 0.00 % is a non-positive overshoot rounded to zero.
