# 5. Design and implementation of the INDI rate controller

This chapter describes the controller that was built: what it is required to do, the control law, why each architectural choice was made and which alternatives were rejected, how the yaw path was refined after measurements, and how the controller is implemented in PX4. Decision identifiers (D-arch-1 and so on) refer to `indi_project/DECISIONS.md`. Equations use the symbols of `src/lib/indi_rate_control/indi_rate_control.{hpp,cpp}`. The PX4 data flow and the PID controller being replaced are described in chapter 4 and are not repeated. Tuning and benchmark results are in later chapters; only the measurements that motivated a design change are quoted here. Where `plan/architecture.md` and the code differ, the code is followed and the difference is listed in section 5.8.

## 5.1 Requirements and scope

The controller is stage 1 of the project: it replaces only the angular-rate control law of a multicopter (the inner loop, `mc_rate_control`). The following are unchanged: the attitude loop (`mc_att_control`), the position loop, the control allocator and its prioritisation (thrust, then roll/pitch, then yaw), airmode, the gyro and gyro-derivative filtering in the sensors module, and the PID rate controller library (`src/lib/rate_control/`). Outer-loop (linear-acceleration) INDI is stage 2 and starts only after stage 1 has passed the held-out scenarios.

The requirements that drive the design are:

1. **PID stays the default.** `MC_RATE_CTL_TYPE` defaults to 0 (PID). With the default, the flown behaviour is the existing PX4 behaviour (the PID branch is the old code, re-indented).
2. **Standard flight modes keep working.** The controller publishes the same `vehicle_torque_setpoint` and `vehicle_thrust_setpoint` as the PID, so every mode, the allocator and failsafes see no difference.
3. **No windup, safe on the ground.** Saturation, landing, disarming and invalid data must not produce unbounded or non-finite output (D-arch-6).
4. **Fair comparison.** The controller must not obtain an advantage that a retuned PID could also have. This rule (D-session3-1) is why, for example, the yaw filtering added in 5.4 is only kept because PID already has an equivalent.
5. **Static memory, deterministic runtime.** No allocation in the control loop; fixed-size state.

## 5.2 Control law

### 5.2.1 Notation

All quantities are per body axis (roll, pitch, yaw), element-wise.

| Symbol | Code name | Meaning | Unit |
|---|---|---|---|
| $\omega$, $\omega_{sp}$ | `rate`, `rate_sp` | measured and desired body rate | rad/s |
| $a_f$ | `angular_accel`, `_a_f` | filtered angular acceleration, `vehicle_angular_velocity.xyz_derivative` | rad/s$^2$ |
| $K$ | `_gain_k` | rate-tracking bandwidth | rad/s |
| $\nu$ | `nu`, `_nu` | virtual control: desired angular acceleration | rad/s$^2$ |
| $\tau_{alloc}$ | `torque_allocated_prev`, `t_alloc` | normalised torque the allocator actually produced from the previous command | 1 |
| $\tau_{act}$ | `_t_act` | modelled actuator torque | 1 |
| $H$ | `_lpf`, `_alpha` | filter chain matching the one that produced $a_f$ | |
| $\tau_f$ | `t_f`, `_t_f` | filtered modelled torque | 1 |
| $G_1$, $G_2$ | `_g1`, `_g2_yaw` | control effectiveness, yaw rotor spin-up term | rad/s$^2$ per unit torque; rad/s$^2$ per unit torque rate |
| $\Delta\tau$ | `dt_cmd`, `_dt_cmd` | torque increment | 1 |
| $\tau_{cmd}$ | return value of `update()` | normalised torque command to the allocator | 1 |
| $T_s$ | `dt` | controller cycle time | s |

Normalised torque is the unit of `vehicle_torque_setpoint`: dimensionless, in $[-1,1]$, with 1 the allocator's reference maximum for that axis.

### 5.2.2 Incremental law

INDI starts from the rigid-body rate dynamics, linearised in the torque about the current operating point:

$$
\dot\omega = \dot\omega_0 + G_1\,(\tau - \tau_0)
$$

where $(\dot\omega_0,\tau_0)$ is a past measurement of acceleration and of the torque that produced it. Choosing the torque so that $\dot\omega$ equals the desired value $\nu$ gives the increment

$$
\Delta\tau = G_1^{-1}\,(\nu - \dot\omega_0)
$$

The reference acceleration is the measurement $a_f$, which already contains everything that moves the vehicle (gyroscopic terms, aerodynamic drag, gusts, centre-of-mass offset); none of it has to be modelled. The torque the measurement corresponds to is not the last command but what the motors actually produced, so the controller adds the increment to the modelled achieved torque $\tau_f$. For roll and pitch, in the order of the code:

$$
\begin{aligned}
e &= \omega_{sp}-\omega, & \nu &= K\odot e\\
\tau_{act}[k] &= \tau_{act}[k-1] + \alpha_a\,\big(\mathrm{sat}_{1}(\tau_{alloc}) - \tau_{act}[k-1]\big), & \alpha_a &= 1-e^{-T_s/T_a}\\
\tau_f &= H\!\big(z^{-d}\,\tau_{act}\big)\\
\Delta\tau &= \mathrm{sat}_{\Delta_{max}}\!\Big(G_1^{-1}\,(\nu - a_f)\Big)\\
\tau_{cmd} &= \mathrm{sat}_{1}(\tau_f + \Delta\tau)
\end{aligned}
$$

with $T_a$ = `MC_INDI_ACT_TC`, $d$ = `MC_INDI_DELAY` samples, $\Delta_{max}$ = `MC_INDI_DT_MAX` and $\mathrm{sat}_L$ the symmetric clamp to $[-L,L]$.

With a perfect $G_1$ and perfect synchronisation, substituting into the plant gives $\dot\omega = \nu$, hence $\dot e = -K e$ for a constant setpoint: a first-order rate response $\omega/\omega_{sp} = K/(s+K)$. $K$ is therefore a physical bandwidth in rad/s (defaults 20, 20, 10 for roll, pitch, yaw). The setpoint feed-forward term $K_{ff}\,\dot\omega_{sp}$ of the architecture draft is not implemented (see 5.8).

There is no integrator. A constant disturbance moment shows up in $a_f$ and is cancelled at the acceleration level; the steady-state acceleration error is zero by construction.

### 5.2.3 Relation to an incremental PID

With fixed $G_1$ and $\tau_f = H(A(\tau))$ the law is algebraically an incremental PID (Acquatella 2017, eq. 29-30, `acquatella2017`). The practical consequence, kept in view for the whole project, is that any benchmark gain must be attributable to what INDI does differently: (i) the feedback is the modelled *achieved* torque, not the commanded one, (ii) the measured acceleration rejects unmodelled moments immediately, (iii) saturation is handled without an integrator. Gains that a retuned PID also obtains must not be credited to INDI. This is why the PID baseline is tuned with the same budget and cost (D-session3-1).

### 5.2.4 Actuator-state estimate and filter synchronisation

The measured $a_f$ is the backward difference of the gyro after notch and a second-order low pass at `IMU_GYRO_CUTOFF`, followed by a first-order `AlphaFilter` at `IMU_DGYRO_CUTOFF` (chapter 4). It is therefore a delayed, smoothed version of the true acceleration. Subtracting it from an un-delayed $\nu$ and adding the result to an un-delayed torque would act on mismatched time scales and destabilise the loop. The incremental form is only valid if $a_f$ and the torque it is paired with, $\tau_f$, have passed through the same filters (Smeur 2016, `smeur2016`, applies the same filter to the gyro-derived acceleration and to the actuator signal; Tal 2021, `tal2021`, Sec. III-B, requires identical low-pass filters for equal phase lag; the Paparazzi implementation, `impl_paparazzi`, passes the actuator state through the same Butterworth as the gyro). The code therefore applies to the modelled torque

$$
H = \underbrace{\mathrm{LPF2p}(\texttt{IMU\_GYRO\_CUTOFF})}_{\texttt{\_lpf}}\ \circ\ \underbrace{\mathrm{AlphaFilter}(\texttt{IMU\_DGYRO\_CUTOFF})}_{\texttt{\_alpha}}
$$

with both cutoffs read from the IMU parameters so that they stay matched when those are changed. Filters are designed at the controller rate $1/T_s$ and redesigned when it moves by more than 10 % (`kRedesignRatio`) or when a cutoff changes; the redesign resets the filter states to the current $\tau_{act}$, so no transient is introduced. A cutoff $\le 0$ makes a stage pass-through, as in the sensor chain.

Two approximations remain and are documented rather than hidden. First, the sensor filters run at the raw gyro rate and ours at the controller rate; in the Gazebo x500 both are 250 Hz (IMU rate from `x500_base/model.sdf`, architecture.md section 10), so they coincide in SITL. Second, the backward difference adds half a raw sample of delay and the publication adds up to one period of transport delay; an integer delay of `MC_INDI_DELAY` samples (0 to 4, default 0) on $\tau_{act}$ is available to absorb that, but half a sample cannot be represented. Notch filters are not replicated (default off in the IMU settings; if enabled the INDI synchronisation would be wrong: a limitation, 5.7).

### 5.2.5 Yaw: rotor spin-up term and yaw filters

Yaw torque comes from rotor drag, and changing yaw torque means accelerating rotors, whose inertia produces a reaction torque proportional to the rate of change of the commanded torque. Following the torque-space form of Smeur 2016, yaw adds a term $G_2\,\dot\tau$:

$$
\dot\omega_z = a_f + G_1\,\Delta\tau + G_2\,\frac{\Delta\tau - (\tau_f-\tau_{f,prev})}{T_s}
$$

Setting $\dot\omega_z=\nu_z$ and solving gives the yaw increment implemented in `update()`:

$$
\Delta\tau_z = \frac{\nu_z - a_{f,z} + \dfrac{G_2}{T_s}\,(\tau_{f,z}-\tau_{f,z,prev})}{G_1 + \dfrac{G_2}{T_s}}
$$

For roll and pitch $G_2/T_s$ is set to 0 in the loop, which recovers 5.2.2. With the default $G_2=0$ (not identifiable from the yaw step data, D-g1-v1) the yaw axis is the same law as the other two with its own $G_1$.

Three further low-pass filters at one common cutoff `MC_INDI_YAW_CUT` act only on yaw. They are optional, off by default, and are introduced and justified in 5.4. Written with $L_f$ for a second-order low-pass at that cutoff and $z$ for the yaw component:

$$
a_{f,z}\leftarrow L_f(a_{f,z}),\qquad \tau_{f,z}\leftarrow L_f(\tau_{f,z}),\qquad \nu_z = K_z\,L_f(\omega_{sp,z}-\omega_z)
$$

The first two are applied to the pair in the same way, so the pair stays synchronised. Disabled means bypassed, not pass-through, so that behaviour with the parameter at 0 is bit-identical to the code without the filters (checked by a unit test, 5.6).

### 5.2.6 Effectiveness $G_1$

$G_1$ is a fixed per-axis parameter (D-arch-5, not adapted online). It was identified from in-loop rate steps in SITL (D-g1-v1): roll = pitch = 241 rad/s$^2$ (fits 237 and 245, R$^2$ 0.94-0.95), yaw 7.4 rad/s$^2$ (fits 7.2-7.6), source `results/sync_check_v0.md`, overlay `bench/params/indi_v1.params`. Identification is a one-off step, not a tuning variable: $G_1$ is identified first, then $K$, `MC_INDI_ACT_TC` and the attitude gains are tuned. Two alternatives were rejected. The first identification, an open-loop fit on PID logs (321 and 211), gave different values for the two axes of a symmetric vehicle and fitted worse. Adaptive estimation (LMS in Smeur 2016, RLS in Blaha 2024, `blaha2024`) is deferred as the first extension if payload or plant-mismatch scenarios show that $G_1$ errors dominate. That a fixed $G_1$ is adequate for stage 1 is an assumption, not a cited result: it is tested by the model-mismatch scenarios, not assumed.

The plant is nonlinear in the actuator: in Gazebo thrust $\propto \omega_{rotor}^2$ with $\omega_{rotor}$ linear in the motor command, while the allocator assumes thrust linear in command (`THR_MDL_FAC` = 0). $G_1$ is therefore operating-point dependent (roughly proportional to rotor speed near hover). The PID has the same mismatch; INDI sees it as a $G_1$ error. $G_1$ is a hover-point value.

## 5.3 Architecture choices

Each choice below lists the decision, the reason and the alternatives that were rejected. The common theme is minimal intrusion into PX4: the controller must be selectable, comparable with the PID on the same airframe, and removable.

### 5.3.1 Torque space ahead of the allocator (D-arch-1)

**Chosen.** INDI outputs a normalised torque and publishes the normal `vehicle_torque_setpoint`. The allocator, its thrust > roll/pitch > yaw prioritisation and airmode work unchanged, and every flight mode that works with the PID works with INDI.

**Rejected: actuator-space INDI** ($u = u_{prev} + B^{+}(\nu - a)$, one increment per motor). It needs either a new allocator input or bypassing the allocator, which loses prioritisation, airmode and the standard modes, and the earlier PX4 attempt (PR #25216, `impl_px4_prior`) drew reviewer requests for no changes to `ControlAllocator`. It remains a possible later branch. The price of the choice is that the actuator model has to live in torque space (5.3.3).

### 5.3.2 Selection inside `mc_rate_control`, law in a new library (D-arch-2)

**Chosen.** A new library `src/lib/indi_rate_control/` holds the law and its unit tests; the PID library is untouched. `mc_rate_control` gets one enum parameter `MC_RATE_CTL_TYPE` (0 PID, 1 INDI) and branches around the single call to the law. The selection is latched while disarmed: a change in flight applies at the next arming, because switching laws mid-air is a transient nobody needs.

**Rejected: a separate module chosen in the startup script.** It would leave the PID module byte-identical, but would duplicate acro-mode setpoint generation, thrust and battery handling, autotune hooks and status publishing, and would put two publishers on the torque topic, which is a hazard. **Rejected: the external-mode pattern of `mc_nn_control` / `mc_raptor`**, which bypasses the allocator and standard modes and is the wrong fit for a rate law.

### 5.3.3 Actuator state from a first-order torque-space model (D-arch-3)

INDI needs the torque the vehicle is producing now, $\tau_f$. There is no measurement of it in SITL: Gazebo's `esc_status.esc_rpm` only echoes the command (integration analysis), as on any vehicle without RPM telemetry. An onboard model is therefore required.

**Chosen (stage 1).** The model input is the allocated torque, i.e. the previous cycle's published `vehicle_torque_setpoint` minus `control_allocator_status.unallocated_torque` (the latter only if the allocator status is newer than the previous torque publication, otherwise the unmodified previous setpoint). The model is a discrete first-order lag with time constant `MC_INDI_ACT_TC` (default 0.02 s, between the x500 values 0.0125 s rising and 0.025 s falling). Using the allocated and not the commanded torque is what makes saturation harmless (5.3.5).

**Rejected: ESC feedback** (gz echoes the command, so it would add nothing). **Rejected: a per-motor model.** The allocator's normalisation scale is not published, so mapping per-motor states back to normalised torque needs a copy of the effectiveness matrix, which would couple the controller to one airframe's allocator and break the torque-space interface. The torque-space lag is exact when no motor is saturated and the rising and falling time constants are equal, and is wrong by their asymmetry otherwise. The trigger to upgrade is recorded in D-arch-3: the benchmark shows that motor asymmetry or saturation limits performance.

### 5.3.4 Filter matching by filtering the model, not the measurement (D-arch-4)

The synchronisation of 5.2.4 could be obtained either by filtering the modelled torque like the measurement, or by changing the sensor filters. **Chosen:** apply $H$ to the modelled torque, reading `IMU_GYRO_CUTOFF` and `IMU_DGYRO_CUTOFF`, and leave the shared IMU filter defaults alone. **Rejected:** retuning the shared sensor filters for INDI, because they are shared with the PID D-term and every axis. If tuning later shows that INDI needs a higher `IMU_DGYRO_CUTOFF`, it is a per-controller parameter set and the retuned PID gets the same freedom (D-session3-1). A pure delay on $\tau_{act}$ is provided for residual lag identified in flight.

### 5.3.5 Saturation, arming and landing (D-arch-6)

- **Saturation.** $\tau_{cmd}=\tau_f+G_1^{-1}(\nu-a_f)$ has no accumulator, and $\tau_f$ follows what the allocator produced. A saturated axis therefore cannot wind up: when the allocator clips the command, the modelled torque is the clipped one and the next increment is computed from it. $\tau_{cmd}$ is clamped to $[-1,1]$ and each increment to $\pm$`MC_INDI_DT_MAX` (default 1, no extra limit). Rejected: copying the PID anti-windup (conditional integration, integral clamp), which is the machinery INDI is meant not to need.
- **Landed or maybe landed.** Ground contact makes $a_f\approx 0$ whatever the torque, so an incremental loop would integrate. The law holds the actuator model and filters at zero ($\tau_f=0$) so the output is the bounded proportional term $G_1^{-1}(\nu-a_f)$, mirroring the PID freezing its integrator. Rejected: letting the law run normally on the ground.
- **Disarmed, first run, selection change.** All dynamic states are reset to zero, once per cycle while disarmed.
- **Invalid data** is handled by a reset and zero output with a fault flag (5.5.4).

### 5.3.6 What INDI replaces and what it does not

INDI replaces the call to `RateControl::update()`, and with it the PID's P, I, D and feed-forward terms. It does not replace the sensors-side filtering, thrust (passed through from `vehicle_rates_setpoint.thrust_body`) or the allocator. Two PID-branch-only steps are skipped on the INDI branch: the 2 Hz yaw output low-pass (`MC_YAW_TQ_CUTOFF`) and battery scaling. A low-pass after the INDI output would sit in series with the actuator, which the law assumes is described by $\tau_f$ alone, and would break the synchronisation. Battery-voltage effects change $G_1$, which the incremental form partly absorbs; the gz simulation has no battery model, so this is untested. The gain-compression step is also PID-only. `rate_ctrl_status` is published only on the PID branch because its integrator fields are meaningless for INDI.

## 5.4 Yaw-path refinements, in chronological order

The architecture of 5.2 and 5.3 was frozen first (session 5) and flown. The roll and pitch paths needed no change. The yaw path needed three, each triggered by a measured excess of control effort (motor-command rate RMS, "effort") relative to PID, and each applied before tuning continued. They share one parameter, `MC_INDI_YAW_CUT`, which grew in scope; the order matters because each step corrected what the previous one left.

### 5.4.1 D-yawfilt: low-pass on the synchronised yaw pair (session 7)

*Problem.* The identified $G_1$ for yaw is small (7.4), so the yaw acceleration noise reaches the yaw torque with gain $1/G_{1,z}$, four times the gain of the first (unidentified) value of 30. Hover effort was already 8 times the PID's with $G_{1,z}=30$ (0.300 against 0.037 per second, `results/sync_check_v0.md` section 3) and rose to 1.616 (44 times PID) with $G_{1,z}=7.4$ (`results/yawcut_check_s8.md`).

*Chosen.* An extra second-order low-pass on the yaw axis, `MC_INDI_YAW_CUT` (Hz, 0 = off), applied identically to $a_{f,z}$ and to $\tau_{f,z}$ so that the synchronisation of 5.2.4 holds. It costs yaw phase lag only; yaw bandwidth is low anyway because yaw is drag-torque limited. For fairness, PID's own yaw output filter `MC_YAW_TQ_CUTOFF` enters the PID tuning space.

*Alternatives rejected.* Inflating $G_{1,z}$ above the identified value (this is what the first version did by accident): it detunes the cancellation and hides the model in a gain. Lowering `IMU_DGYRO_CUTOFF`: shared with PID's D-term and all axes, while roll and pitch noise were already at PID's level. Reusing `MC_YAW_TQ_CUTOFF` on the INDI output: filtering after the increment breaks synchronisation.

*Measured effect* (hover, seed 1, `results/yawcut_check_s8.md`, one flight each, smoke level): a 10 Hz cutoff reduced hover effort from 1.616 to 0.228 (PID 0.037), a 7-fold reduction, confirming the diagnosis; step_yaw effort did not change (3.69 against 3.77, PID 0.559), so it came from the step response and not from noise, which led to the next two steps.

### 5.4.2 D-yawnu: the yaw rate used in $\nu$ is filtered too (session 11)

*Problem.* With $a_{f,z}$ and $\tau_{f,z}$ filtered at PID's 2 Hz, hover effort was still about 2.1 times PID's (`results/tuning/r2f_yc2.md`). The remaining chatter was gyro noise in $\nu_z = K_z(\omega_{sp,z}-\omega_z)$, which reaches the torque with gain $K_z/G_{1,z}\approx 0.8$.

*Chosen.* When `MC_INDI_YAW_CUT` > 0, the measured yaw rate in $\nu$ passes through a third low-pass of the same design (the setpoint was left unfiltered at this stage). One knob then sets the yaw noise bandwidth of every feedback path of the yaw increment, as `MC_YAW_TQ_CUTOFF` does for PID's whole yaw output. A cutoff of 0 stays bit-identical to the preceding code. Results of rounds 1 and 2 were obtained with the old semantics and are labelled accordingly.

*Alternatives rejected.* Filtering the whole yaw increment (adds lag in series with the actuator and breaks the $a_f/\tau_f$ synchronisation). Only shrinking $K_z$: the tuner already had $K_z$ in its space and settled at 5.8, and lowering it trades away yaw tracking that is INDI's measured advantage. A separate parameter: it enlarges the tuning space for a knob whose physical meaning (yaw noise bandwidth) is the same.

*Measured effect* (hover, seeds 1-3, `results/yawnu_check_s11.md`): hover motor-rate effort 0.077-0.080 before, 0.041-0.043 after, against 0.037 for PID, i.e. about 2.1 times down to about 1.1 times; yaw torque change per sample dropped from 0.0003 to 0.0000.

### 5.4.3 D-yawsp: the setpoint is filtered as well (session 13)

*Problem.* After D-yawnu and a tuning round centred at lower yaw gains (D-r3), one INDI penalty remained under the frozen cost: step_yaw effort was about 5 times PID's (4.66-5.89). Measurement (`bench/yaw_step_effort.py`, quoted in D-r3): on each 45 degree yaw step the setpoint term $K_z\,\omega_{sp,z}/G_{1,z}$ peaked at 2.75 normalised torque (the rate setpoint was 3.49 rad/s, clipped by the yaw rate limit), so yaw torque hit its limit of 1.0, against a PID peak of 0.33. Motor-rate RMS around the step was 11.1 against 1.55 for PID (7 times). PID smooths the same step with its default 2 Hz yaw torque output filter; INDI passed it through unfiltered.

*Chosen.* $\nu_z = K_z\,L_f(\omega_{sp,z}-\omega_z)$: the filter acts on the rate error, setpoint included (firmware 99634a6b71). This gives INDI the structure PID already has by default, so it is not an advantage offered only to INDI.

*Alternatives rejected.* A separate yaw setpoint pre-filter parameter (one more parameter for the same effect; D-r3 also rejected it earlier as unfair to PID unless offered to both). Changing the effort metric or its weight: the cost is frozen (`bench/scenarios.md` v1), and changing it after seeing INDI lose would be after-the-fact selection. Lowering $K_z$ further: r3 already showed yaw tracking degrading while the torque step remained, since it scales with $K_z$.

*Measured effect* (`results/tuning/r3f_yawsp.md`, candidate c13, seeds 1-3, 15 flights): step_yaw effort ratio to PID 1.42 (was 4.66-5.89); on seed 1 motor-rate RMS around the steps 1.13 (4.70 before, PID 0.79) and peak yaw torque 0.45 (0.78 before, PID 0.33). Cost: step_yaw score ratio 0.876 to 1.056, the lag PID also pays with its 2 Hz filter. Roll and pitch were unchanged within noise, as expected for a yaw-only change.

A consequence is that the library header describes `MC_INDI_YAW_CUT` as a filter on three signals: $a_{f,z}$, $\tau_{f,z}$ and the yaw rate error. Its default stays 0, so the stand-alone law is unfiltered; the tuning rounds from r3 on are centred at 2 Hz (D-r3).

## 5.5 Implementation in PX4

### 5.5.1 Files

| File | Content |
|---|---|
| `src/lib/indi_rate_control/indi_rate_control.{hpp,cpp}` | the law, class `IndiRateControl`, no PX4 module dependencies |
| `src/lib/indi_rate_control/indi_rate_control_test.cpp` | gtest unit tests (5.6) |
| `src/modules/mc_rate_control/MulticopterRateControl.{hpp,cpp}` | selection, parameter wiring, allocator feedback, `runIndiRateControl()`, status publication |
| `src/modules/mc_rate_control/mc_rate_control_params.yaml` | `MC_RATE_CTL_TYPE` and `MC_INDI_*` |
| `msg/IndiRateStatus.msg`, `msg/CMakeLists.txt`, `src/modules/logger/logged_topics.cpp` | the `indi_rate_status` topic, registered and logged |

The module depends on the library through its CMake `DEPENDS`. The PID library and `ControlAllocator` are not modified.

### 5.5.2 Runtime selection and cycle

`MulticopterRateControl::Run()` is triggered by each `vehicle_angular_velocity` sample, as for the PID. While the vehicle is disarmed (or not a rotary wing) the module latches `_use_indi = (MC_RATE_CTL_TYPE == 1)`, resets the INDI states and zeroes the stored previous torque; first run, change of selection and disarm are therefore the same code path. When armed with `_use_indi`, each cycle:

1. reads $\omega$ and $a_f$ from `vehicle_angular_velocity` (`xyz`, `xyz_derivative`) and the rate setpoint as for the PID, with the module's `dt` clamped to [0.000125, 0.02] s;
2. builds $\tau_{alloc}$: the previously published torque, minus the stored `unallocated_torque` if the allocator status timestamp is newer than that publication;
3. calls `IndiRateControl::update(rates, rate_setpoint, angular_accel, torque_allocated_prev, dt, landed)` with `landed = _maybe_landed || _landed`;
4. publishes `indi_rate_status` and then the usual `vehicle_torque_setpoint` and `vehicle_thrust_setpoint` (thrust unchanged, a non-finite torque component is replaced by 0 as in the PID branch). The published torque is stored for the next cycle.

On the PID branch the code is as before (re-indented). `IMU_GYRO_CUTOFF` and `IMU_DGYRO_CUTOFF` are read with `param_get` in `parameters_updated()` and passed to `setFilterCutoffs()`.

### 5.5.3 Parameters

All are only used when `MC_RATE_CTL_TYPE` = 1. Values are the firmware defaults; the identified and tuned values are applied by parameter overlays in `indi_project/bench/params/` and are reported in the tuning chapters.

| Parameter | Default | Range | Unit | Meaning |
|---|---|---|---|---|
| `MC_RATE_CTL_TYPE` | 0 (PID) | 0, 1 | enum | rate law, latched while disarmed |
| `MC_INDI_G1_R` | 320 | 0.001-5000 | rad/s$^2$ per unit torque | roll effectiveness |
| `MC_INDI_G1_P` | 210 | 0.001-5000 | same | pitch effectiveness |
| `MC_INDI_G1_Y` | 30 | 0.001-5000 | same | yaw effectiveness (not identified for any airframe) |
| `MC_INDI_G2_Y` | 0 | 0-1 | rad/s$^2$ per unit torque rate | yaw spin-up term, 0 disables |
| `MC_INDI_K_R`, `_K_P`, `_K_Y` | 20, 20, 10 | 1-100 | rad/s | rate-tracking bandwidth |
| `MC_INDI_ACT_TC` | 0.02 | 0.001-0.2 | s | actuator lag time constant |
| `MC_INDI_DELAY` | 0 | 0-4 | cycles | pure delay on the modelled torque |
| `MC_INDI_DT_MAX` | 1.0 | 0.01-1 | unit torque | per-cycle, per-axis increment limit |
| `MC_INDI_YAW_CUT` | 0 (off) | 0-100 | Hz | yaw low-pass, 5.4 |

The firmware defaults for $G_1$ (320, 210, 30) are the first estimates from open-loop PID logs, not the later in-loop values (241, 241, 7.4) of D-g1-v1; the latter are used through the overlay. Because $G_{1,z}$ is unidentified for other airframes, a different airframe must identify $G_1$ before using INDI.

### 5.5.4 Numerical edge cases

| Case | Handling in the code |
|---|---|
| Non-finite `rate`, `rate_sp`, `angular_accel` or previous torque; `dt` outside [0.000125, 0.02] s | `update()` calls `reset()`, sets `fault`, returns zero torque for that cycle. The module also clamps `dt` before the call, so only invalid sensor data triggers it in practice. |
| Zero, negative, NaN $G_1$ (below `kMinG1` = 1e-3) or negative or non-finite $K$ | same: `paramsValid()` is checked every cycle, so a bad parameter set never divides. The parameter minimum already excludes most of these. |
| Non-finite $G_2$, cutoffs, delay | setters sanitise: $G_2$ <= 0 or NaN becomes 0; `ACT_TC` clamped to [0.001, 0.2] s and NaN replaced by 0.02; filter and yaw cutoffs <= 0 or NaN become 0 (off / pass-through); delay clamped to 0-4; `DT_MAX` <= 0 or NaN becomes 1. |
| Overflow in $\Delta\tau$ from absurd inputs | the increment is checked for finiteness before use, with the same reset-and-fault outcome. |
| Allocated torque outside [-1, 1] | clamped before the actuator model, so a corrupt allocator value cannot overflow the lag. |
| Zero thrust | thrust is not used by the law (torque space, no thrust-dependent scaling); the law's output is bounded whatever the thrust. Whether the allocator can realise the torque at low thrust is the allocator's concern and appears in $\tau_{alloc}$. |
| Saturation | 5.3.5: no accumulator; $\tau_f$ follows the allocated torque; clamps on $\Delta\tau$ and $\tau_{cmd}$. |
| Landed | `resetStates()` every cycle, so $\tau_f=0$, delay buffer and filters are cleared and the output is the bounded term $G_1^{-1}(\nu-a_f)$. After take-off the filters start from zero, consistent with the actuator model. |
| Disarm, first run, selection change | `_indi.reset()` and `_prev_torque_setpoint.zero()` in the disarm block. |
| Loop-rate change > 10 % or cutoff change | filters redesigned, states settled at the current values (no transient). |
| Yaw cutoff >= 0.45 x sample rate | treated as disabled (stricter than `LowPassFilter2p`, which disables at 0.5). |

The `fault` flag in `indi_rate_status` makes a rejected cycle visible in the log. Static memory only: `Vector3f` state, ring buffer of $5$ samples (`kMaxDelaySamples`+1), fixed filter objects.

### 5.5.5 uORB message and logging

`indi_rate_status` (`msg/IndiRateStatus.msg`) is published by `mc_rate_control` only while INDI is selected, every cycle:

| Field | Type | Content |
|---|---|---|
| `timestamp` | uint64 | microseconds |
| `nu[3]` | float32 | desired angular acceleration $\nu$ used (rad/s$^2$) |
| `angular_accel_filtered[3]` | float32 | $a_f$ used, after the yaw low-pass if enabled |
| `torque_filtered[3]` | float32 | $\tau_f$ used, after the yaw low-pass if enabled |
| `torque_increment[3]` | float32 | $\Delta\tau$ (clamped) |
| `fault` | bool | inputs or parameters rejected this cycle |

It is added with `add_optional_topic("indi_rate_status")` at full rate, so tuning and the report can plot the synchronisation ($a_f$ against $\tau_f$) directly. `nu[2]` reports the yaw value actually used, which is filtered when `MC_INDI_YAW_CUT` > 0.

## 5.6 Unit tests

`indi_rate_control_test.cpp` contains 18 gtests (14 after the first yaw-cutoff change, 18 after D-yawnu and D-yawsp; `plan/integration_log.md` records 14 of 14 passing, and `results/unittest_s13.log` records the ctest target passing in session 13 without a per-test count). They use a simulated roll plant (rigid body, first-order actuator, $G_1$ = 100, acceleration filtered like PX4's gyro derivative, 400 Hz). They cover:

- **Zero in, zero out:** zero inputs for 400 cycles give exactly zero torque and no fault.
- **Closed-loop rate step:** a 1 rad/s step reaches 95 % within 0.5 s, overshoots less than 20 % and settles to within 5 %, torque bounded (expected first-order response).
- **Disturbance rejection without an integrator:** a constant moment disturbance of $-30$ rad/s$^2$ is driven to a rate below 0.05 rad/s within 2 s.
- **No windup:** the allocated torque is clipped to $\pm0.05$ for 2 s under a large setpoint, then released; the rate returns below 0.05 rad/s with bounded, finite output.
- **Landed:** with a constant rate error and no measured acceleration, the output equals the bounded proportional increment (0.1 here) and the filtered torque stays zero.
- **Invalid input:** NaN and infinity on each input, zero $G_1$, and bad $\Delta t$ give zero output and a fault, with state reset.
- **Yaw $G_2$:** with $G_2$ = 0 yaw equals the roll/pitch form; a non-zero $G_2$ changes the yaw output only.
- **Filter design:** a sample-rate change redesigns the filters without a transient; pass-through filters and the pure delay behave as specified.
- **Yaw cutoff (D-yawfilt):** cutoff 0 leaves outputs unchanged; noise on the yaw acceleration input gives lower yaw output deviation (below 0.7 times) with roll and pitch equal; enabling causes no transient; invalid cutoffs (NaN, infinity, negative, 120 Hz) disable the filter.
- **Yaw rate filter (D-yawnu, D-yawsp):** cutoff 0 unchanged, noise reduction on the yaw rate path with roll/pitch equal, steady-state $\nu_z=K_z(\omega_{sp,z}-\omega_z)$, and smoothing of a yaw setpoint step.

These tests check the algebra and the safety behaviour in a linear idealised plant. They do not check the synchronisation against the real sensor chain, a multi-axis plant, or the PX4 module wiring; those are covered only by the SITL benchmark.

## 5.7 Limitations

- **Torque-space actuator model.** A single first-order lag per axis cannot represent motor asymmetry (different rising and falling constants) or per-motor saturation; the error is bounded by the asymmetry in normal flight and unquantified in heavy saturation or motor loss.
- **Fixed $G_1$.** It is a hover-point value for one airframe, and effectiveness varies with rotor speed. There is no online adaptation; payload, battery and airframe changes are errors in $G_1$.
- **$G_{1,z}$ and $G_2$.** The yaw effectiveness is small and noisy, and $G_2$ was not identifiable (left at 0). The yaw filters are a pragmatic noise control, not a model.
- **Synchronisation is approximate.** Half a raw sample of difference delay cannot be represented by an integer delay; notches are not replicated; filter matching assumes the IMU filters run at the controller rate.
- **No battery model.** Battery scaling is skipped for INDI and the simulator has no battery sag; its effect was not tested.
- **No setpoint feed-forward**, no gain compression, no autotune support for INDI.
- **Simulation only.** Gazebo x500; no hardware flights, no real motor lag or rotor-speed measurement.
- **Single airframe, single loop rate.** The parameters were identified at 250 Hz on the x500.

## 5.8 Discrepancies found

Notes where `plan/architecture.md` and the code differ; the chapter follows the code.

- Note: architecture.md says `K_ff` defaults to 0 and gives $\nu = K\odot(\omega_{sp}-\omega)+K_{ff}\,\dot\omega_{sp}$; code has no `K_ff` and no setpoint derivative, $\nu = K\odot(\omega_{sp}-\omega)$ only.
- Note: architecture.md says the allocated torque uses `unallocated_torque` "only when fresher than 20 ms"; code uses it only when the allocator status timestamp is newer than the previous torque publication (no 20 ms limit).
- Note: architecture.md says that for non-finite inputs the law outputs a "zero torque increment"; code returns a zero torque vector (total command zero) after resetting all states.
- Note: architecture.md says the landed output is "$G_1^{-1}\nu$"; code computes $G_1^{-1}(\nu-a_f)$ with $\tau_f=0$. They are equal only if $a_f=0$ on the ground (the unit test supplies $a_f=0$).
- Note: architecture.md says $G_1\le\epsilon$ is validated "at update" and the loop rate uses "the module's clamped dt"; code validates $G_1$ (>= 1e-3) and $K$ (>= 0) in `update()` every cycle, and rejects `dt` outside [0.000125, 0.02] s in the library in addition to the module's clamp to the same interval.
- Note: architecture.md section 6 gives initial $G_1$ 321/211 (open-loop fit) and the integration log 320/210/30 as defaults; the values actually used in the tuned configurations are 241/241/7.4 (D-g1-v1) through an overlay, not the firmware defaults.
- Note: architecture.md describes only the yaw $G_2$ term; the yaw low-pass (D-yawfilt), the filtered rate in $\nu$ (D-yawnu) and the filtered setpoint (D-yawsp) were added later and are not in architecture.md (it was not updated); the code header is current.
- Note: architecture.md cites `wang2019` for tolerance to $G_1$ errors, which is not in `research/sources.md`; it is not used in this chapter.

Unverified: the 18-test count and the test thresholds come from reading `indi_rate_control_test.cpp`; the tests were not re-run for this chapter; the yaw-filter figures are copied from the cited result files and decisions as written.
