# 4. Analysis of the PX4 multicopter control architecture

This chapter describes the part of PX4 that the INDI controller replaces and the parts it must live with. It states what the code does, not what the code should do. All references are to PX4 `main` (merge-base 7d362c6f38 of the working branch). Where a line number points to `MulticopterRateControl.cpp` it refers to `main`, because the working branch has INDI additions that shift lines. Facts were checked against the source; the checking log, including corrections to earlier notes, is in `indi_project/plan/px4_analysis_verification.md`. Delay figures are analytic estimates, not measurements.

## 4.1 Overview and data flow

PX4 controls a multicopter with a cascade of four modules connected by uORB topics. The position loop (not treated here) produces an attitude and thrust setpoint. `mc_att_control` turns the attitude setpoint into a body-rate setpoint. `mc_rate_control` turns the rate setpoint and the measured rate into a normalised torque. `control_allocator` turns torque and thrust into motor commands. The gyro is conditioned upstream by the `vehicle_angular_velocity` publisher in the sensors module.

```
 sensor_gyro(_fifo)                 (raw gyro, kHz)
        |
        v
 sensors/vehicle_angular_velocity   notches -> LPF2p(IMU_GYRO_CUTOFF) -> rate
        |                           difference of filtered rate -> AlphaFilter(IMU_DGYRO_CUTOFF) -> accel
        | vehicle_angular_velocity {xyz, xyz_derivative}   published at IMU_GYRO_RATEMAX (400 Hz)
        v
 mc_rate_control  <-- vehicle_rates_setpoint {roll,pitch,yaw,thrust_body} <-- mc_att_control <-- vehicle_attitude_setpoint
        |   ^                                                                       ^
        |   +-- control_allocator_status (<= every 5 ms) --+                         +-- vehicle_attitude
        |                                                  |
        | vehicle_torque_setpoint (normalised xyz)         |
        | vehicle_thrust_setpoint (normalised xyz, pass-through of thrust_body)
        v                                                  |
 control_allocator  --------------------------------------+
        | actuator_motors (normalised [0,1], NaN = stopped)
        v
 output driver (mixer_module: THR_MDL_FAC inverse, linear map to PWM/DShot/gz velocity) -> ESCs / motors
```

Three scheduling facts matter for a rate-loop replacement. First, `mc_rate_control` has no timer. It is a work item on the `rate_ctrl` queue triggered by each new `vehicle_angular_velocity` sample (`MulticopterRateControl.cpp:50`, `MulticopterRateControl.hpp:109`, `MulticopterRateControl.cpp:69`), so its rate equals the publication rate of the filtered gyro. Second, the control allocator is triggered by each new `vehicle_torque_setpoint` and runs on the same queue (`ControlAllocator.cpp:57,96`); thrust is latched and used only when a torque message arrives (`ControlAllocator.cpp:383-402`). A controller must therefore publish torque every cycle. Third, `timestamp_sample` is propagated from the gyro sample through torque (`MulticopterRateControl.cpp:275`) to `actuator_motors` (`ControlAllocator.cpp:753`), so the whole chain can be time-aligned in logs.

## 4.2 Rate controller

`mc_rate_control` reads the filtered rate $\omega$ and angular acceleration $\dot\omega_f$ from `vehicle_angular_velocity` (`MulticopterRateControl.cpp:139-140`) and the rate setpoint from `vehicle_rates_setpoint`. A non-finite setpoint axis is replaced by the measured rate (`:185-187`), and setpoint values are held between updates. The time step is $\Delta t$ from `timestamp_sample`, clamped to $[0.125, 20]$ ms (`:136`). In acro mode the module generates the rate setpoint itself from the sticks (`:159-182`). It runs only while `flag_control_rates_enabled` is set (`:192`), and it resets its integrator and gain compression when disarmed (`:195-197`).

The control law is a parallel PID with a derivative on measurement, in normalised units (`src/lib/rate_control/rate_control.cpp:75-78`). With element-wise products over the three axes:

$$
\tau = K_p\,(\omega_{sp}-\omega) + I - K_d\,\dot\omega_f + K_{ff}\,\omega_{sp}
$$

The "D term" is thus $-K_d\dot\omega_f$ with $\dot\omega_f$ taken straight from the sensor module; there is no setpoint kick and no filtering inside the controller. The defaults are $K_p=0.15$, $K_i=0.2$, $K_d=0.003$ for roll and pitch (yaw $0.2$, $0.1$, $0$), and $K_{ff}=0$; they are dimensionless torque per rad/s and per rad/s$^2$, not SI.

The integrator is updated after the torque is computed, so it uses the previous state, and only when the vehicle is not landed (`rate_control.cpp:81-83`). Anti-windup has two parts. Each axis is clamped by conditional integration: if the allocator flagged positive saturation the error is limited to $\min(e,0)$, and for negative saturation to $\max(e,0)$ (`rate_control.cpp:92-99`). The error is also attenuated by $i = \max(0,\,1-(e/\mathrm{rad}(400^\circ))^2)$ (`:107-108`), and the state is advanced by forward Euler and clamped to the limit $\pm L_i$ (`:111-115`):

$$
I_{k+1} = \mathrm{sat}_{L_i}\!\big(I_k + i\,K_i\,e_k\,\Delta t\big)
$$

The saturation flags are derived in the module from `control_allocator_status`: when `torque_setpoint_achieved` is false, the sign of `unallocated_torque[i]` beyond `FLT_EPSILON` sets the positive or negative flag (`MulticopterRateControl.cpp:208-224`). A TODO states that the unallocated value itself should be used (`:223`). Flags persist between status messages.

After the law, the module applies optional gain compression (`MC_GC_EN`, off by default; `:232-233`) and always a low-pass on the yaw torque at `MC_YAW_TQ_CUTOFF` (default 2 Hz; `:236`). Non-finite torque components are set to zero (`:249-251`), optional battery scaling multiplies thrust and torque and clips to $[-1,1]$ (`:259-266`), and the result is published (`:271-277`). Thrust is not computed here; it is the `thrust_body` field of the rate setpoint, passed through unchanged (`:188,248`). For VTOL the module is started with an argument that selects the `_virtual_mc` topic variants (`:51-52`). The only unit test of the library is a zero-input case (`rate_control_test.cpp:39-44`).

## 4.3 Attitude controller

`mc_att_control` is triggered by `vehicle_attitude` (`mc_att_control_main.cpp:83,254`) and publishes `vehicle_rates_setpoint` together with the body thrust vector (`:366,382-389`). Its core, `AttitudeControl::update`, is a quaternion proportional law with a reduced-attitude yaw weighting (`AttitudeControl.cpp:153-179`). The error is $e_q = 2\,\mathrm{imag}(q^{-1}q_d)$, the rate setpoint is $\omega_{sp} = K_q\,e_q$ with per-axis gains (`:182-190`), and the result is limited per axis (`:211-213`). On this `main` the desired attitude first passes a second-order critically damped reference model, and the model's error-driven rate, scaled by a feed-forward gain and limit, is added to the setpoint (`:94-137,197-208`). The rate setpoint seen by the rate loop is therefore a smooth, limited signal, but it is a rate, not an angular acceleration: no acceleration setpoint exists anywhere upstream.

## 4.4 Angular-velocity and angular-acceleration estimation and filters

`VehicleAngularVelocity` is triggered by `sensor_gyro_fifo` or `sensor_gyro` and filters every raw sample at the raw gyro rate, which can be several kHz. Publication is throttled by `IMU_GYRO_RATEMAX` (default 400 Hz, range 100-2000, `imu_gyro_parameters.yaml:63-81`; gate at `VehicleAngularVelocity.cpp:930`). The published values are those of the last sample of the processed batch, with no averaging (`:772,855-856`). Consequently the rate loop runs at about 400 Hz while the filters see the full-rate signal.

The rate chain, applied in place in this order, is: dynamic notch from ESC rpm (`IMU_GYRO_DNF_EN`, default 0), dynamic notch from FFT peaks, static notches (`IMU_GYRO_NF*`, off by default), then a second-order Butterworth low-pass `LowPassFilter2p` at `IMU_GYRO_CUTOFF`, default 40 Hz (`:733-773`). The published rate is the calibrated filter output minus the in-run gyro bias (`:937`).

The acceleration estimate is derived from the output of that same chain. For each raw sample it forms a backward difference of the already filtered rate, $a_n = (\omega_{f,n}-\omega_{f,n-1})/T_s$ (`:781`, with $1/T_s$ from the FIFO sample time at `:836`), and feeds it to a first-order `AlphaFilter` at `IMU_DGYRO_CUTOFF`, default 20 Hz (`:782`, `VehicleAngularVelocity.hpp:177`). The published `xyz_derivative` is rotated but not bias-corrected (`:941`). The parameter documentation calls this filter a second-order Butterworth (`imu_gyro_parameters.yaml:84-92`), but the code is a first-order exponential filter, $y \leftarrow y + \alpha(x-y)$ with $\alpha = \Delta t/(\tau+\Delta t)$ and $\tau = 1/2\pi f_c$ (`AlphaFilter.hpp:90,132-135`). Setting the cutoff to 0 disables it (`:183-189`).

At low frequency the group delay of the rate path is about $\sqrt2/(2\pi f_c)\approx 5.6$ ms at 40 Hz. The acceleration path adds the alpha filter with $\tau\approx 8.0$ ms at 20 Hz, so $\dot\omega_f$ lags $\omega$ by roughly 8 ms and the actuator command by more. Both are estimates; the chapter on identification will measure them. Two sharing effects are worth noting. `IMU_GYRO_CUTOFF` affects both signals, so changing it also changes the legacy D term (`imu_gyro_parameters.yaml:52`). And the filter state is re-seeded whenever a cutoff or the sample rate changes (`VehicleAngularVelocity.cpp:163-195`), which causes a short glitch in the acceleration.

## 4.5 Control allocation and saturation

The allocator forms a six-element control vector $c = [M_x\;M_y\;M_z\;F_x\;F_y\;F_z]^\top$ from the torque and thrust setpoints (`ControlAllocator.cpp:414-419`). Torque components that are not finite are zeroed (`:387-391`). The method is selected by `CA_METHOD` (default 2, auto; `module.yaml:50`) and a multirotor requests sequential desaturation with normalised roll/pitch (`ActuatorEffectivenessMultirotor.hpp:47-55`).

The effectiveness matrix is static, rebuilt only on parameter changes. For rotor $i$ with unit axis $a_i$, position $p_i$ relative to the centre of gravity, thrust coefficient $c_{t}$ (`CA_ROTOR*_CT`, default 6.5) and moment ratio $k_m$ (`CA_ROTOR*_KM`, default 0.05), the column is built from

$$
F_i = c_t\,a_i,\qquad M_i = c_t\,(p_i\times a_i) - c_t\,k_m\,a_i
$$

(`ActuatorEffectivenessRotors.cpp:194,197`). The model is linear in the normalised motor command $u\in[0,1]$, although the parameter text speaks of $u^2$ (`module.yaml:211`). There is no rotor inertia, gyroscopic or drag term. The allocator then forms $\text{mix}=\mathrm{geninv}(B)$ and divides its columns by a scale. Roll and pitch share one scale, the larger of $\sqrt{\|\text{mix}_{:,j}\|^2/(n_j/2)}$, $j\in\{\text{roll},\text{pitch}\}$; yaw uses the maximum of its column (`ControlAllocationPseudoInverse.cpp:66-126,155-170`). The scale is fixed at set-up and not refreshed after an actuator failure (`:72`). It is not published. A unit of normalised torque is therefore a geometry-dependent quantity, not a torque in N m, and the same number gives a different angular acceleration on a different airframe. The allocated control reported back uses the same scale (`ControlAllocation.hpp:146-153`).

Desaturation order depends on `MC_AIRMODE`, whose default is 0 (`src/lib/mixer_module/params.yaml:5-21`; switch at `ControlAllocationSequentialDesaturation.cpp:52-64`). With airmode disabled the mix is built without yaw, thrust may only be reduced, then roll and then pitch are scaled down until feasible (`:174-200`), and finally yaw is added and desaturated last, with a small extra headroom above the maximum, followed by a thrust-only reduction (`mixYaw`, `:207-228`). The priority is thus thrust, roll and pitch, then yaw. With airmode on roll/pitch (`:122-143`) or roll/pitch/yaw (`:146-171`) the collective thrust may be raised to keep authority, and yaw is desaturated separately last. After allocation an optional slew-rate limit (only if a slew parameter is set; `ControlAllocator.cpp:111-120,454-456`) and a hard clip to the actuator limits are applied (`:458`).

The feedback to the controller is `control_allocator_status`, published at most every 5 ms (`:469-470`). `unallocated_torque` is the control setpoint minus the allocated control, in the same normalised units (`:675-682`), and `torque_setpoint_achieved` holds when its squared norm is below $10^{-6}$ (`:691-693`). The allocated control is computed from the clipped actuator setpoint, so it contains saturation and slew effects but nothing measured from the motors. The allocator does not apply `THR_MDL_FAC`; the output driver inverts it (`FunctionMotors.hpp:81-105`), and with the default 0 the command-to-thrust mapping is assumed linear.

## 4.6 Actuator feedback available (real hardware vs SITL)

The only measurement of the actuators in the PX4 data model is `esc_status`, an array of `EscReport` with `esc_rpm`, voltage, current and temperature fields, each filled only "if supported" (`msg/EscReport.msg`). `actuator_outputs` is the post-mixer command, not a measurement. `mc_rate_control` does not subscribe to `esc_status`; the one consumer on the control path is the dynamic notch of the gyro filter (`VehicleAngularVelocity.cpp:582-588`).

On hardware, rpm comes from DShot bidirectional telemetry (`DShot.cpp:793,803`, eRPM divided by pole pairs), UAVCAN or Cyphal ESCs (`uavcan/actuators/esc.cpp:141`) and a few other drivers (`TAP_ESC.cpp:298`). Rate and latency of this telemetry were not measured.

In Gazebo SITL the content of `esc_status` is not a measurement. `GZMixingInterfaceESC` subscribes to `/<model>/command/motor_speed` and advertises on the same topic (`GZMixingInterfaceESC.cpp:41-50`); it publishes the mixer outputs as rotor velocity commands (`:98-103`) and builds `esc_status` from that same message, with `esc_rpm = actuators.velocity(i)`, a fixed 50 degree temperature and online and armed flags (`:132-143`). The field named rpm is thus an echo of the command in the output range `SIM_GZ_EC_MIN..MAX` of 150 to 1000 for the x500 (`4001_gz_x500:40-48`), carrying no motor dynamics. No rotor-speed topic is bridged back. Whether the gz motor plugin can publish one could not be verified, because its source is not in the repository. The software-in-the-hole simulator (SIH) differs: its `esc_rpm` is $r_{max}\sqrt{u}$ of a throttle state that already includes a first-order lag with `SIH_T_TAU` (`sih.cpp:481,548`, `aero.hpp:267-269`).

The x500 motor model in Gazebo is a first-order velocity model. All four plugin blocks use `timeConstantUp` 0.0125 s, `timeConstantDown` 0.025 s, `maxRotVelocity` 1000 rad/s, `motorConstant` $8.54858\times10^{-6}$ (thrust $=k\,\Omega^2$), `momentConstant` 0.016, rotor drag $8.06428\times10^{-5}$ and rolling moment $10^{-6}$ (`Tools/simulation/gz/models/x500/model.sdf:11-73`). The vehicle has mass 2.0 kg and inertia $I_{xx}=I_{yy}=0.02167$, $I_{zz}=0.04$ kg m$^2$ (`x500_base/model.sdf:9-16`). Two mismatches with the PX4 side are visible in the files. The PX4 airframe uses `CA_ROTOR*_KM` = 0.05 against the plugin's 0.016, so the allocator's yaw model is wrong by this ratio. And thrust is quadratic in $\Omega$ while $\Omega$ is linear in $u$ (`mixer_module.cpp:565`, `THR_MDL_FAC` unset), whereas the allocator assumes thrust linear in $u$. The discretisation of the time constants inside the plugin is not verifiable here.

## 4.7 How alternative controllers integrate, and why

Two controllers already coexist with the standard chain: `mc_nn_control` and `mc_raptor`. Both are optional modules (started from `rc.mc_apps:49-58` when `MC_NN_EN` or `MC_RAPTOR_ENABLE` is 1) that replace the whole cascade. They register an external mode with an arming check (`mc_nn_control.cpp:295-296`, `mc_raptor.cpp:259-263`; `mc_raptor` can also take over the OFFBOARD mode through `MC_RAPTOR_OFFB`), request the setpoint type `TYPE_DIRECT_ACTUATORS` (`mc_nn_control.cpp:319`, `mc_raptor.cpp:529`) and publish `actuator_motors` directly (`mc_nn_control.cpp:533`, `mc_raptor.cpp:864-885`). The commander maps that setpoint type to a control mode with no flag set (`setpoint_types.cpp:51-53`), so `flag_control_rates_enabled` is false and `mc_rate_control` stays idle (`MulticopterRateControl.cpp:192`), and `flag_control_allocation_enabled` is false, so the allocator does not publish (`ControlAllocator.cpp:363-368,747-749`). Exclusion is by control-mode flags driven by the active mode, not by a check in `mc_rate_control`.

The reason for this design is that a neural policy outputs motor commands from state and has no use for a torque interface or the attitude cascade, so it needs a mode in which the standard loops are disabled. The price is a separate flight mode: the controller is not active in Stabilized, Position or Mission, and the allocator, with its prioritisation and failure handling, is bypassed. For a rate-loop law that must operate inside the standard modes and downstream of the same attitude loop, this pattern is the wrong shape, but it demonstrates the registration and flag mechanism and that two controllers may coexist when exactly one publishes `actuator_motors`.

## 4.8 Implications for INDI

The architecture poses a set of questions that the design must answer. They are listed here without answers.

1. Placement. The only point where angular acceleration, rate and rate setpoint are all available is the rate loop, and its output contract is a normalised torque. Should the incremental law publish torque ahead of the allocator, or actuator commands, and what does each choice do to the allocator's prioritisation, airmode and failure handling? How is the choice between the PID and the INDI law made, and when may it change?
2. Units. The allocator's normalised torque is dimensionless and geometry-dependent, and the scale is not published. How is the control effectiveness $G$, in rad/s$^2$ per unit of normalised torque, obtained per airframe: from inertia and the matrix, or by identification?
3. Reference signal. There is no angular acceleration setpoint. How is the desired acceleration formed from a rate setpoint, and does the feed-forward of the attitude reference model have a role?
4. Synchronisation. The measured acceleration lags the rate by several milliseconds through filters that are shared with other parameters and live at a different sample rate from the controller. What signal stands for the previous actuator state, and how is it brought to the same delay and gain as the acceleration estimate? Which filter parameters may be changed without disturbing the PID?
5. Actuator state. In Gazebo `esc_status` is an echo and carries no dynamics, while hardware telemetry is partial and its latency is unknown. What model of the motors, and in which space, supplies the actuator state, and how is it kept consistent with what the allocator actually achieved?
6. Saturation. The allocator clips and desaturates after the controller, and its status arrives at most every 5 ms and only reports static saturation. How is the incremental state kept from winding up, and how are airmode and the yaw-last priority taken into account?
7. Existing post-processing. The yaw torque low-pass, gain compression and battery scaling sit after the PID law. Which of them apply to an incremental law, and which would break its time alignment?
8. Operating states. The PID freezes only its integrator when landed and resets when disarmed. What happens to the incremental state on the ground, at arming, at a parameter change and at a filter re-initialisation?
9. Loop rate. The controller runs at the publication rate of the gyro (400 Hz by default) with a $\Delta t$ clamped to $[0.125, 20]$ ms. How sensitive is the law and its synchronisation filter to this rate?
10. Fairness of comparison. Since the PID can be retuned against the same filters, what must be held equal in the benchmark so that gains are not attributed to INDI that a retuned PID also obtains?
