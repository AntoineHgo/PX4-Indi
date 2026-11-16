# Effective PID rate-loop gains, reference SITL airframe (4040_gz_quad5in)

Paths relative to /home/ahugo/Documents/Drotek/Codes/PX4-Indi.

## 1. Gain table

Precedence: runner env/overlay > airframe `param set-default` > module default.
"set by" is the layer that determines the value the loop actually sees.

| Parameter | value | source file:line | set by airframe/runner/default |
|---|---|---|---|
| MC_ROLLRATE_P | 0.03 | ROMFS/px4fmu_common/init.d-posix/airframes/4040_gz_quad5in:70 | airframe (module default 0.15 at src/modules/mc_rate_control/mc_rate_control_params.yaml:11) |
| MC_ROLLRATE_I | 0.06 | 4040_gz_quad5in:71 | airframe (module default 0.2 at mc_rate_control_params.yaml:22) |
| MC_ROLLRATE_D | 0.0006 | 4040_gz_quad5in:72 | airframe (module default 0.003 at mc_rate_control_params.yaml:43) |
| MC_ROLLRATE_K | 1.0 | NOT FOUND in airframe or runner | default (mc_rate_control_params.yaml:71) |
| MC_ROLLRATE_FF | 0.0 | NOT FOUND in airframe or runner | default (mc_rate_control_params.yaml:53) |
| MC_PITCHRATE_P | 0.03 | 4040_gz_quad5in:73 | airframe (default 0.15 at mc_rate_control_params.yaml:82) |
| MC_PITCHRATE_I | 0.06 | 4040_gz_quad5in:74 | airframe (default 0.2 at mc_rate_control_params.yaml:93) |
| MC_PITCHRATE_D | 0.0006 | 4040_gz_quad5in:75 | airframe (default 0.003 at mc_rate_control_params.yaml:114) |
| MC_PITCHRATE_K | 1.0 | NOT FOUND in airframe or runner | default (mc_rate_control_params.yaml:141) |
| MC_PITCHRATE_FF | 0.0 | NOT FOUND in airframe or runner | default (mc_rate_control_params.yaml:123) |
| MC_YAWRATE_P | 0.1 | 4040_gz_quad5in:76 | airframe (default 0.2 at mc_rate_control_params.yaml:152) |
| MC_YAWRATE_I | 0.05 | 4040_gz_quad5in:77 | airframe (default 0.1 at mc_rate_control_params.yaml:163) |
| MC_YAWRATE_D | 0.0 | 4040_gz_quad5in:78 | airframe (default 0.0 at mc_rate_control_params.yaml:184) |
| MC_YAWRATE_K | 1.0 | NOT FOUND in airframe or runner | default (mc_rate_control_params.yaml:211) |
| MC_YAWRATE_FF | 0.0 | NOT FOUND in airframe or runner | default (mc_rate_control_params.yaml:193) |
| MC_ROLL_P | 8.0 | 4040_gz_quad5in:79 | airframe, attitude (outer) loop, not in rate law (default 4.0 at src/modules/mc_att_control/mc_att_control_params.yaml:11) |
| MC_PITCH_P | 8.0 | 4040_gz_quad5in:80 | airframe, attitude (outer) loop (default 4.0 at mc_att_control_params.yaml:22) |
| MC_YAW_P | 3.0 | 4040_gz_quad5in:81 | airframe, attitude (outer) loop (default 2.8 at mc_att_control_params.yaml:33) |
| MC_INDI_* | NOT SET | airframe: no match. runner: only MC_INDI_EN / MC_INDI_W_MAX, and only when the scenario overlay sets MC_RATE_CTL_TYPE=1 (indi_flight/bench/run_scenario.py:648-652) | not on the default PID path |
| IMU_GYRO_CUTOFF | 40 Hz | indi_flight/bench/run_scenario.py:39 and :674 (PX4_PARAM_IMU_GYRO_CUTOFF) | runner (module default 40.0 at src/modules/sensors/vehicle_angular_velocity/imu_gyro_parameters.yaml:56) |
| IMU_DGYRO_CUTOFF | 20 Hz | indi_flight/bench/run_scenario.py:39 and :675 | runner (module default 20.0 at imu_gyro_parameters.yaml:97) |
| IMU_GYRO_RATEMAX | scenario rate (800 default per help text at run_scenario.py:589) | indi_flight/bench/run_scenario.py:673 | runner (module default 400 at imu_gyro_parameters.yaml:79) |

Runner check: `grep -n "param set\|IMU_\|MC_" indi_flight/bench/run_scenario.py` shows no literal MC_*RATE_P/I/D/K/FF override. The scenario overlay dict (lines ~625-655) can still inject arbitrary parameter names at run time, which this grep would not catch.

## 2. Control law (src/lib/rate_control/rate_control.cpp)

Gain assembly, src/modules/mc_rate_control/MulticopterRateControl.cpp:
```
83: const Vector3f rate_k = Vector3f(_param_mc_rollrate_k.get(), _param_mc_pitchrate_k.get(), _param_mc_yawrate_k.get());
85: _rate_control.setPidGains(
86:     rate_k.emult(Vector3f(..._rollrate_p..)),   // P_eff = K * P
87:     rate_k.emult(Vector3f(..._rollrate_i..)),   // I_eff = K * I
88:     rate_k.emult(Vector3f(..._rollrate_d..)));  // D_eff = K * D
93: _rate_control.setFeedForwardGain(
94:     Vector3f(_param_mc_rollrate_ff.get(), _param_mc_pitchrate_ff.get(), _param_mc_yawrate_ff.get()));   // FF NOT multiplied by K
```

Update law, rate_control.cpp:
```
36:  Vector3f rate_error = rate_sp - rate;
71:  Vector3f RateControl::update(const Vector3f &rate, const Vector3f &rate_sp, const Vector3f &angular_accel,
78:  Vector3f torque = _gain_p.emult(rate_error) + _rate_int - _gain_d.emult(angular_accel) + _gain_ff.emult(rate_sp);
82:  if (!landed) { updateIntegral(rate_error, dt); }
111:  float rate_i = _rate_int(i) + i_factor * _gain_i(i) * rate_error(i) * dt;
```
(i_factor = max(0, 1 - (rate_error/radians(400))^2), rate_control.cpp:20-21.)

Call site, MulticopterRateControl.cpp:140, 229-233:
```
140: const Vector3f angular_accel{angular_velocity.xyz_derivative};
229: torque_setpoint = _rate_control.update(rates, _rates_setpoint, angular_accel, dt, _maybe_landed || _landed);
232: torque_setpoint = _gain_compression.getGains().emult(torque_setpoint);   // nonlinear gain compression, applied after the PID
```

D acts on the measured angular acceleration (`xyz_derivative` of the gyro, filtered by IMU_DGYRO_CUTOFF), with a NEGATIVE sign: torque_D = -K*D*alpha. Equivalent to +K*D*d(rate_error)/dt for constant setpoint, so it is damping.

The FF term is `+ FF * rate_sp` with no K factor (rate_control.cpp:78, MulticopterRateControl.cpp:93-94). It is zero here.

## 3. Effective linear gains (torque per unit, before control allocation)

Using the airframe values and K = 1.0 (default, not overridden):

- effective P gain = K * P: roll 1.0 * 0.03 = 0.03 (N·m per rad/s); pitch 0.03; yaw 1.0 * 0.1 = 0.1
- effective I gain = K * I: roll 0.06 (N·m per rad); pitch 0.06; yaw 0.05
- effective D gain = K * D: roll 0.0006 (N·m per rad/s²), applied as -D_eff * alpha_meas; pitch 0.0006; yaw 0.0
- effective FF = FF (not times K): 0.0 on all axes

Linear model: tau = P_eff*(rate_sp - rate) + I_eff*integral(rate_sp - rate) - D_eff*d(rate)/dt + FF*rate_sp, then multiplied by the gain-compression factor (nonlinear; MC_GC_EN default not verified in gain_compression_params.yaml).

## Caveats

- MC_GC_EN default: NOT VERIFIED (gain_compression_params.yaml excerpt read only showed FW_GC_* entries).
- MC_*RATE_K default 1.0 confirmed at mc_rate_control_params.yaml:71, :141, :211.

## Orchestrator check (S37)
- Units correction: the rate controller output is NORMALISED torque (vehicle_torque_setpoint, [-1, 1]), not N·m. Read
  every "N·m" above as normalised torque; P in 1/(rad/s), I in 1/rad, D in 1/(rad/s^2).
- Gain compression: `MC_GC_EN` default 0 (`src/lib/rate_control/gain_compression_params.yaml:30`), not set by the
  airframe or the runner, so `getGains()` is 1 and the PID rate loop is linear for G2. The runner overlay dict must
  not set MC_GC_EN on margin runs (assert in S39 plumbing).
- Sign: the law subtracts D times measured angular acceleration; in the loop gain this is the +Kd s F_d term of
  note 4.2 / 7.2 (loop broken at the torque, feedback path).
