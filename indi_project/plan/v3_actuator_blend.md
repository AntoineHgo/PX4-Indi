# v3 draft (session 42): complementary actuator state to restore integral action

Status: DRAFT design, not implemented, not flown. Motivation: `results/s2_tilt_diag.md`.

## Problem

The INDI law is t_cmd = t_s + (nu - a_f)/G1, where t_s is the actuator state expressed as torque.

- v1: t_s = model(t_cmd), a first-order lag filtered like the gyro. In steady state t_s = t_cmd, so nu = 0. The law
  integrates, and any constant torque gap is removed (T8 motor loss: roll/pitch 5-9x better than PID).
- v2: t_s = f(measured eRPM). If the actuators do not deliver what the allocator asks for (motor gain loss,
  EC_MIN/MAX change, ESC mapping error, battery sag), t_s != t_cmd in steady state. Then nu = G1 (t_cmd - t_s) != 0,
  which means a standing rate error and a steady tilt (13-14 deg on V motor_loss_0, all seeds).
- v1's weakness was the opposite one: at high frequency the model state is wrong when ACT_TC is mismatched, which
  produced the H5 5-7 Hz limit cycle. v2's measured state fixed that.

## Proposal: D-v3-blend (draft)

Use the measurement at high frequency and the model at low frequency:

    t_s = t_meas + LP_Tb( t_model - t_meas )

- t_model is the v1 model state (`ACT_TC`, eRPM delay-matched), and LP_Tb is a first-order low-pass with time
  constant Tb (new parameter, e.g. `MC_INDI_ACT_BLD`, in seconds).
- In steady state t_s = t_model = t_cmd, so nu = 0 and the integral action returns.
- Above 1/(2 pi Tb), t_s follows t_meas, which keeps v2's robustness to ACT_TC mismatch, as long as 1/(2 pi Tb) is
  well below the 5-7 Hz H5 limit cycle. Start value: Tb = 0.3 s (0.5 Hz).
- Limits: Tb -> infinity gives v2, Tb -> 0 gives v1. One parameter, bounded, no state beyond one filter per axis.
  Reset it on arming like the other INDI filters. When eRPM is lost (the existing fallback), t_s = t_model.

## Alternatives (rejected, to be confirmed)

- Rate-error integrator added to nu: a PID-like I term. It needs anti-windup, adds a gain, and blurs the INDI-vs-PID
  comparison.
- Adaptive G1 / effectiveness (Smeur-style): it estimates the torque-per-command slope, but the gap here is in the
  command-to-output map, which adaptive G1 does not close unless the adaptation also takes in that map. Heavier, and
  needs persistent excitation.

## Honesty constraints

- Held-out V results are now known. v3 results on V must be labelled post-hoc, or a new held-out set must be frozen
  before v3 flies. Recommendation: freeze a small V' (different motor, fault magnitude 0.6 and 0.8, a gain error on
  two motors, sag to 0.75) before the first v3 flight.
- Screen under O-12 first: watchdog, then 1 seed of motor_loss_0, mismatch_combined_rate and step_roll at Tb in
  {0.1, 0.3, 1.0}; drop any Tb that brings back the H5 limit cycle or loses step tracking against v2.
- The frozen v2 V and seen-set results stay in the report as the v2 outcome.
