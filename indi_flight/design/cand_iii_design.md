# G3 step (c) candidate (iii): bounded rate integrator (S235, fixed before any (iii) flight)

Candidate (ii) (per-motor map correction) MISSED (joint and draw 264 lost control). (iii) is the brief's second option.

## Mechanism
With the measured torque as feedback (t_f = t_meas + 1 s blend), a constant actuator effectiveness loss (draw 264 weak
motor 0.709, trim about 0.08 growing with collective) is already inside t_meas, so the INDI increment (K e - a) / G1
is a proportional law around a torque it cannot hold: steady rate error e = gap G1 / K. A rate integrator supplies
the held torque.

## Law (roll, pitch, yaw, per axis i; frame: body FRD; units in brackets)
    e_i      = rate_sp_i - rate_i                                [rad/s] (yaw: the filtered yaw error already used in nu)
    di_i/dt  = w_i K_i e_i / G1_i,   |i_i| <= RI_LIM             [normalised torque / s], i_i in normalised torque
    nu_i     = K_i e_i + G1_i i_i                                [rad/s^2]
that is nu = K (1 + w_i / s) e, w_i = min(2 pi MC_INDI_RI_FREQ, 0.2 K_i) [rad/s], K the effective gain
(0.5x until MC_INDI_ID_OK). The rest of the law (lead, G2 yaw spin-up, increment limit, measured path, blend,
ACT_BLD 1.0) is unchanged. The integral enters nu, so it passes through the same 1/G1 inversion and the yaw G2 low pass.

## Where
`src/lib/indi_rate_control` (`IndiRateControl::setRateIntegral`, `setSaturationStatus`, `updateRateIntegral`, step 7 of
`update()`); `McIndiRateControl` feeds the saturation flags and sets the parameters; `rate_integral` added to
`indi_rate_status` for the log. Stock files untouched.

## Anti-windup, landed, arming, telemetry loss
- Saturation: the module derives per-axis positive/negative saturation from `control_allocator_status`
  (`!torque_setpoint_achieved` and sign of `unallocated_torque`, the stock `mc_rate_control` rule). Error in the
  saturated direction is zeroed before integrating (conditional integration, as stock `RateControl::updateIntegral`);
  the opposite direction still unwinds. Bound: |i| <= MC_INDI_RI_LIM.
- Landed or maybe_landed: state frozen (no update). While landed it is also not applied to nu (the landed law stays the
  proportional increment, no bias on the ground); in flight with maybe_landed it is applied and held.
- Arming: the module calls `reset()` every cycle while disarmed, which clears the state; `reset()` also runs after
  the fault hold expires. A single rejected cycle keeps the state and does not integrate.
- Telemetry loss/frozen rpm: the integrator uses no rpm; the measured path falls back to the model as before and
  the integral keeps acting on the rate error.

## Values (fixed here, no sweep)
- Rate loop crossover about K = 20 rad/s (MC_INDI_K_R/P/Y 20 in g5_freeze_s157; the lead makes the loop first
  order with e' = -K e). Corner MC_INDI_RI_FREQ = 0.5 Hz = 3.14 rad/s = K/6.4, below the 1/5 rule (4 rad/s), also
  enforced in code (w_i <= 0.2 K_i). Phase cost at crossover: atan(3.14/20) = 8.9 deg, so the G2 rate phase margin
  >= 45 deg loses < 9 deg and the margin stays > 45 deg provided it was >= 54 deg; the integral time constant
  (0.32 s) is well inside the 1 s blend, so the gap is removed within ~1 s at 3 rad/s error.
- MC_INDI_RI_LIM = 0.2 normalised torque: the weak-motor trim is about 0.08 (growing with collective, estimated up to
  ~0.12 near full collective); 0.2 covers it with margin 1.7x yet is only 20 % of the torque range, so a runaway cannot
  command more than 0.2 on top of the proportional part. The increment limit MC_INDI_DT_MAX 1.0 is unchanged.
- Defaults in the yaml equal these values; cand_iii.params also lists them explicitly.

## What would show it wrong
- Log (`indi_rate_status.rate_integral`): on draw 264 it does not reach about -0.08 on roll/pitch within ~1.5 s of the
  fault, or sits at the limit (gap larger than the bound, or the integrator is fighting something else).
- G2 rate cells: margin below 45 deg or a new low-frequency oscillation (around 0.5 Hz) in healthy flights.
- Flights: 262/283 worse than baseline, or integrator charged at landing/takeoff (frozen/landed logic).
- Integral action acts on rate error, so a persistent rate setpoint that the vehicle cannot follow (saturation) is
  guarded only by the allocator flags; a saturation that the allocator does not report would wind to the limit.
