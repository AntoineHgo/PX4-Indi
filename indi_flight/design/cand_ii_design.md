# G3 step (c) candidate (ii): per-motor map correction (S233, fixed before any (ii) flight)

## Mechanism
The INDI actuator model takes the torque the allocator produced from the previous setpoint
(`torque_allocated_prev` = torque setpoint - unallocated torque) and assumes each motor gives
omega_i^2 / omega_max^2 = u_cmd,i (the allocator's normalised thrust). Candidate (ii) learns one gain per motor

    k_i = LPF_tau(u_meas,i) / LPF_tau(u_cmd,i),   u_meas,i = (omega_i / omega_max)^2 from ESC rpm

and adds the torque of the map error to the model input:

    torque_allocated_prev += M(k o u_cmd) - M(u_cmd)

with M the rotor effectiveness of the measured-torque path (same CA_ROTOR geometry, trim and scale). The rest of
the rate law is unchanged; ACT_BLD stays 1.0 (FREEZE-10). Both filters run only while learning is allowed, so the
ratio is a weighted mean over the allowed samples only.

## Where
- `src/lib/indi_rate_control/motor_map_correction.{hpp,cpp}`: class `MotorMapCorrection` (filters, freeze, bound,
  arming reset); unit tests in `motor_map_correction_test.cpp`.
- `src/modules/mc_indi_rate_control`: `McIndiRateControl::runIndiRateControl` feeds it per cycle (command from
  `actuator_motors`, fresh/frozen rpm sample from `IndiMeasuredTorque::motorThrust()`, allocator
  `actuator_saturation[i]`, landed, armed) and applies the torque delta. New parameters in the module yaml.

## Values (fixed here, no sweep)
- `MC_INDI_MAP_TC` = 0.2 s (time constant of both filters; 0 disables). 10x the rate-loop response and > 4x
  ACT_TC 0.05 s, so it does not fight the rate loop or follow the motor lag, yet the 264 weak-motor gap (which grew over
  ~1 s with collective through the 1 s blend) is learned in ~0.6 s (95 %).
- `MC_INDI_MAP_LIM` = 0.5: k_i bounded to [0.5, 1.5]; 0.709 lies inside, a broken rpm cannot change the model torque
  by more than half of a motor's share.
- Learning floor: u_cmd,i >= 0.05 (constant): idle commands give no usable ratio.

## Frozen (k_i held, filters not updated) when
landed (or maybe landed); disarmed; motor i rpm sample not fresh (telemetry loss, offline, stale, implausible) or
frozen (existing ERPM_FRZ detection); allocator reports motor i saturated (any non-OK `actuator_saturation`), which
is the anti-windup: a clipped command does not teach a wrong gain. Reset to k = 1 and empty filters on each arming.
Disabled when W_MAX = 0 (no rpm).

## Why it removes the draw-264 gap
Draw 264 (weak motor 3 at 0.709 + saturation): the measured torque already sees the weak motor, the model does not.
t_fb = LPF_tb(t_model) + HPF_tb(t_meas), so the model/measurement difference reaches t_fb through the 1 s blend,
and it is proportional to collective (k-1) * u_cmd,3: as collective grows the trim gap grows faster than the blend
follows, and INDI integrates a wrong increment (restore264 / falsifier_s222). With k_3 -> 0.709 the model torque
equals the measured one at every collective (multiplicative map, no lag as collective grows), so the blend has
nothing to lag and no low-frequency bias remains; the 1 s blend keeps its noise role. Motors at the allocator limit
freeze their gain, and the unallocated-torque feedback already covers the clipped part.

## What would show it wrong
- Log: k_3 does not settle near 0.709 within ~1 s after the fault, or healthy k_i drift away from 1 by > 0.1 in
  hover (rpm-to-command scale inconsistent, then the map correction injects a bias of its own).
- Flight: draw 264 / joint LOC or item 1-2 failures persist with k_3 learned (gap not the LOC cause), or 262/283
  get worse than baseline (correction couples with cmd/rpm delay in manoeuvres).
- Unverified before flight: that the sim weak motor reduces rotor speed (rpm-visible) rather than only thrust per
  rpm. If it is thrust-only, u_meas cannot see it and k_3 stays at 1 (candidate is then inert, (iii) is next).
