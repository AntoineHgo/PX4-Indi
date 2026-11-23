# INDI Multicopter Controllers (Advanced)

:::warning
The INDI controllers are optional and experimental.
They are not part of the default PX4 configuration, and they need hardware that stock PX4 does not require (see [Requirements](#requirements)).
Read the [Limitations](#limitations) before flying.
:::

This topic explains how to enable and configure the optional Incremental Nonlinear Dynamic Inversion (INDI) controllers for multicopters.
Two modules are provided:

- `mc_indi_rate_control` replaces the PID rate controller (`mc_rate_control`).
- `mc_indi_pos_control` replaces the position controller (`mc_pos_control`) in every flight mode that uses it.
  It runs the stock position control followed by an INDI acceleration stage.

Each module is enabled by its own parameter, and an INDI module is never started together with its stock counterpart.
The two modules are started independently: you can enable the INDI rate controller with the stock position controller, or the INDI position controller with the stock rate controller.
They are designed to be used together.
Only multicopters are supported: the start script does not start the INDI modules for VTOL vehicles, and the rate controller only runs while the vehicle is a multicopter.

## Overview

INDI depends less on a vehicle model than a conventional controller.
Instead of computing the control output from a model of the whole vehicle, it computes only the _change_ in control output needed to move from the currently measured angular acceleration (rate loop) or linear acceleration (position loop) to the demanded one.
Anything that is already present in the measurement, such as drag, small imbalances or a thrust offset, does not have to be modelled.
Only the control effectiveness, the response of the vehicle to a unit change in the actuators, has to be known.

To know what the actuators are actually producing, the controllers use the measured rotor speed of each motor, reported by the ESCs (for example over bidirectional DShot), instead of assuming that the motors followed the commands.
The rate controller converts the rotor speeds into a measured torque, and the position controller converts them into a measured mean rotor thrust.
If the rotor-speed measurement of a motor is missing or stale, the controllers fall back to a first-order actuator model (see [MC_INDI_ERPM_TO](../advanced_config/parameter_reference.md#MC_INDI_ERPM_TO) and [MC_INDI_ERPM_FRZ](../advanced_config/parameter_reference.md#MC_INDI_ERPM_FRZ)).

## Requirements

The vehicle must be a multicopter with a configured [control allocator](../concept/control_allocation.md), and must meet the following requirements.

- **Rotor-speed telemetry on every motor.**
  Use an ESC protocol that reports rotor speed to the flight controller, for example bidirectional DShot.
  The INDI controllers do not block arming if it is missing.
  If the rotor speed of a motor is missing or stale, the controllers use the actuator model instead (see [Overview](#overview)), which is less accurate.
- **Rotor geometry in the `CA_*` parameters.**
  The rotor positions, spin directions, and thrust and moment coefficients must be configured, because the measured torque is computed with the control allocation library.
  See [Actuator Configuration](../config/actuators.md).
- **Each enabled INDI module starts before the first arm.**
  One controller must run from arming to disarming.
  There is no stock controller to fall back to if an INDI module fails to start.
- **A correct GNSS delay.**
  Set [SENS_GNSS0_DELAY](../advanced_config/parameter_reference.md#SENS_GNSS0_DELAY) within 50 ms of the measured latency of the GNSS receiver.
  The outer loop is less tolerant of a stale position measurement than the PID controller.

## Enabling the Controllers

The modules are not included in every board configuration.
Of the boards in the PX4 source tree, only the simulation target `px4_sitl_default` builds them.
For any other board, enable these options in the board configuration (for example with `make <target> boardconfig`):

- `CONFIG_MODULES_MC_INDI_RATE_CONTROL` (requires `CONFIG_MODULES_CONTROL_ALLOCATOR`)
- `CONFIG_MODULES_MC_INDI_POS_CONTROL` (requires `CONFIG_MODULES_MC_POS_CONTROL`)

On a board where a module is not built in, its enable parameter does not exist and the stock controller starts.

To enable the controllers:

1. Set [MC_INDI_EN](../advanced_config/parameter_reference.md#MC_INDI_EN) to `1` to use the INDI rate controller.
1. Set [MC_INDI_POS_EN](../advanced_config/parameter_reference.md#MC_INDI_POS_EN) to `1` to use the INDI position controller.
1. Reboot the vehicle (both parameters require a reboot).

The INDI rate controller refuses to start if another controller is already publishing `vehicle_torque_setpoint`.

:::info
[Autotune](../config/autotune_mc.md) identifies and writes the PID rate gains, so it is not started when the INDI rate controller is enabled.
:::

## Physical Parameters

The INDI rate controller needs a few physical parameters of the airframe.
The defaults of the control effectiveness and yaw spin-up parameters (`MC_INDI_G1_*` and `MC_INDI_G2_Y`) are the values of a reference 5-inch quadcopter.
They are not a substitute for values that match your vehicle.

| Parameter                                                                                  | Meaning                                                          |
| ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| [MC_INDI_G1_R][MC_INDI_G1_R], [MC_INDI_G1_P][MC_INDI_G1_P], [MC_INDI_G1_Y][MC_INDI_G1_Y] | Angular acceleration (rad/s^2) per unit of normalised torque     |
| [MC_INDI_G2_Y][MC_INDI_G2_Y]                                                               | Yaw rotor spin-up term                                           |
| [MC_INDI_W_MAX][MC_INDI_W_MAX]                                                             | Rotor speed (rad/s) at full thrust, used for the measured torque |
| [MC_INDI_ACT_TC][MC_INDI_ACT_TC]                                                           | Actuator (motor) time constant                                   |

### Identification

The physical parameters are identified in flight by the INDI controller itself, without flying under PID first.
The vehicle flies a short excitation manoeuvre while INDI controls it in a conservative configuration, and the parameters are then fitted to the logged response.

- **Before identification has run**, [MC_INDI_ID_OK](../advanced_config/parameter_reference.md#MC_INDI_ID_OK) is `0`.
  The vehicle then applies the rate bandwidth gains ([MC_INDI_K_R](../advanced_config/parameter_reference.md#MC_INDI_K_R), [MC_INDI_K_P](../advanced_config/parameter_reference.md#MC_INDI_K_P) and [MC_INDI_K_Y](../advanced_config/parameter_reference.md#MC_INDI_K_Y)) at half their set value.
- **After identification**, enter the identified values and set `MC_INDI_ID_OK` to `1`, which applies the gains as set.
- The excitation is generated by the `MC_INDI_INJ_*` and `MC_INDI_PINJ_*` parameters.
  They are for bench and identification use only and are off by default.

:::info
The tooling that runs the identification and fits the parameters is not yet described in this page.
:::

If you are unsure of a value, round the actuator time constant up: an over-estimate of up to twice the true motor time constant keeps the stability margins, an under-estimate does not.
Under-estimating the yaw spin-up term `MC_INDI_G2_Y` is benign, over-estimating it is the weak side of the margin.
`MC_INDI_W_MAX` defaults to `0`, which disables the measured torque: the controller then uses its actuator model.

## Gains and Tuning

The defaults are intended to be flown without further tuning once the physical parameters are set.
The parameters that a user may adjust are:

| Parameter                                                                          | Default  | Effect                                                                  |
| ---------------------------------------------------------------------------------- | -------- | ----------------------------------------------------------------------- |
| [MC_INDI_K_R][MC_INDI_K_R], [MC_INDI_K_P][MC_INDI_K_P], [MC_INDI_K_Y][MC_INDI_K_Y] | 20 rad/s | Closed-loop rate tracking bandwidth per axis                            |
| [MC_INDI_XY_P][MC_INDI_XY_P]                                                       | 1.2 1/s  | Horizontal position gain (replaces `MPC_XY_P`)                          |
| [MC_INDI_XY_VP][MC_INDI_XY_VP]                                                     | 2.4 1/s  | Horizontal velocity gain (replaces `MPC_XY_VEL_P_ACC`)                  |
| [MC_INDI_LEAD][MC_INDI_LEAD]                                                       | 1        | Rate lead scale: 0 disables it, and higher values raise motor noise     |
| [MC_INDI_YAW_CUT][MC_INDI_YAW_CUT]                                                 | 0 Hz     | Extra low-pass on the yaw feedback: 0 disables it                       |

Raise the bandwidth gains slowly, and land before changing a parameter.
Leave the remaining `MC_INDI_*` parameters (delays, timeouts, filter and blend constants, slew limits) at their defaults unless the bench checks below show a problem.

## Pre-Flight Bench Checks

Before the first flight with the INDI controllers, check the following on the bench (propellers removed):

1. **Both modules run.**
   Check that each enabled module is running: run `mc_indi_rate_control status` and `mc_indi_pos_control status` in the MAVLink shell.
   The command only reports whether the module is running (it prints no further statistics).
   There is no stock fallback, so a module that failed to start means that the vehicle has no rate or position controller.
1. **Rotor-speed telemetry rate and latency.**
   Check that every motor reports rotor speed at a rate consistent with the controller rate, and with a latency that is small and similar across motors.
   The controller compensates a fixed latency with [MC_INDI_ERPM_DLY](../advanced_config/parameter_reference.md#MC_INDI_ERPM_DLY) and [MC_INDI_POS_DLY](../advanced_config/parameter_reference.md#MC_INDI_POS_DLY), in controller cycles.
1. **Frozen-value behaviour.**
   A motor whose reported rotor speed stays bit-identical while its command varies is treated as offline after [MC_INDI_ERPM_FRZ](../advanced_config/parameter_reference.md#MC_INDI_ERPM_FRZ) seconds, and the measured torque falls back to the actuator model.
   Check that the ESC driver does not repeat stale values in a way that hides a missing measurement.
1. **Loop timing.**
   Check in the log that the rate and position modules run at their configured rates without missed cycles.
1. **GNSS latency.**
   Measure the latency of the receiver and set `SENS_GNSS0_DELAY` within 50 ms of it.

## Limitations

- The INDI controllers replace the stock controllers in every flight mode, and there is no PID fallback in flight.
- Autotune is not available with the INDI rate controller.
- Every motor should provide rotor-speed telemetry: arming is not blocked without it, and the controllers then use the less accurate actuator model.
- The INDI rate controller does not start if another controller already publishes `vehicle_torque_setpoint`.
  If another publisher appears while it is running, it logs an error but keeps running.
- Only multicopters are supported; VTOL vehicles are not.

:::warning
TODO(owner): robustness limits pending.
:::

## Parameter Reference

The full list, with ranges and long descriptions, is in the [Parameter Reference](../advanced_config/parameter_reference.md).
Search for `MC_INDI_` to find the groups _Multicopter INDI Rate Control_ and _Multicopter INDI Position Control_.

| Parameter                            | Default | Unit  | Description                                              |
| ------------------------------------ | ------- | ----- | -------------------------------------------------------- |
| [MC_INDI_EN][MC_INDI_EN]             | 0       |       | Use the INDI rate controller (reboot required)           |
| [MC_INDI_POS_EN][MC_INDI_POS_EN]     | 0       |       | Use the INDI position controller (reboot required)       |
| [MC_INDI_ID_OK][MC_INDI_ID_OK]       | 0       |       | Physical parameters identified (0: gains applied at 0.5x) |
| [MC_INDI_G1_R][MC_INDI_G1_R]         | 1757.0  |       | Roll control effectiveness                               |
| [MC_INDI_G1_P][MC_INDI_G1_P]         | 1640.0  |       | Pitch control effectiveness                              |
| [MC_INDI_G1_Y][MC_INDI_G1_Y]         | 205.0   |       | Yaw control effectiveness                                |
| [MC_INDI_G2_Y][MC_INDI_G2_Y]         | 27.0    |       | Yaw rotor spin-up term                                   |
| [MC_INDI_W_MAX][MC_INDI_W_MAX]       | 0       | rad/s | Rotor speed at full thrust (0: measured torque disabled) |
| [MC_INDI_K_R][MC_INDI_K_R]           | 20.0    | rad/s | Roll rate bandwidth                                      |
| [MC_INDI_K_P][MC_INDI_K_P]           | 20.0    | rad/s | Pitch rate bandwidth                                     |
| [MC_INDI_K_Y][MC_INDI_K_Y]           | 20.0    | rad/s | Yaw rate bandwidth                                       |
| [MC_INDI_ACT_TC][MC_INDI_ACT_TC]     | 0.05    | s     | Actuator time constant                                   |
| [MC_INDI_LEAD][MC_INDI_LEAD]         | 1       |       | Rate lead scale                                          |
| [MC_INDI_DELAY][MC_INDI_DELAY]       | 0       |       | Actuator model delay (cycles)                            |
| [MC_INDI_ERPM_DLY][MC_INDI_ERPM_DLY] | 1       |       | Measured torque delay (cycles)                           |
| [MC_INDI_ERPM_TO][MC_INDI_ERPM_TO]   | 0.02    | s     | Measured torque timeout                                  |
| [MC_INDI_ERPM_FRZ][MC_INDI_ERPM_FRZ] | 0.5     | s     | Frozen rotor speed detection time                        |
| [MC_INDI_ACT_BLD][MC_INDI_ACT_BLD]   | 1.0     | s     | Actuator state blend time constant                       |
| [MC_INDI_DT_MAX][MC_INDI_DT_MAX]     | 1.0     |       | Maximum torque increment per cycle                       |
| [MC_INDI_LND_SLEW][MC_INDI_LND_SLEW] | 5.0     | 1/s   | Landed feedback torque slew (normalised torque per second) |
| [MC_INDI_SP_TO][MC_INDI_SP_TO]       | 0.5     | s     | Rate setpoint timeout                                    |
| [MC_INDI_YAW_CUT][MC_INDI_YAW_CUT]   | 0       | Hz    | Yaw feedback low-pass cut-off                            |
| [MC_INDI_POS_LPF][MC_INDI_POS_LPF]   | 10.0    | Hz    | Acceleration and thrust filter cut-off                   |
| [MC_INDI_POS_DLY][MC_INDI_POS_DLY]   | 1       |       | Measured thrust delay (cycles)                           |
| [MC_INDI_POS_TB][MC_INDI_POS_TB]     | 0.3     | s     | Collective blend time constant                           |
| [MC_INDI_XY_P][MC_INDI_XY_P]         | 1.2     | 1/s   | Horizontal position gain                                 |
| [MC_INDI_XY_VP][MC_INDI_XY_VP]       | 2.4     | 1/s   | Horizontal velocity P gain                               |

The `MC_INDI_INJ_*` and `MC_INDI_PINJ_*` parameters are for bench and identification use only and are not listed.

<!-- prettier-ignore-start -->
[MC_INDI_EN]: ../advanced_config/parameter_reference.md#MC_INDI_EN
[MC_INDI_POS_EN]: ../advanced_config/parameter_reference.md#MC_INDI_POS_EN
[MC_INDI_ID_OK]: ../advanced_config/parameter_reference.md#MC_INDI_ID_OK
[MC_INDI_G1_R]: ../advanced_config/parameter_reference.md#MC_INDI_G1_R
[MC_INDI_G1_P]: ../advanced_config/parameter_reference.md#MC_INDI_G1_P
[MC_INDI_G1_Y]: ../advanced_config/parameter_reference.md#MC_INDI_G1_Y
[MC_INDI_G2_Y]: ../advanced_config/parameter_reference.md#MC_INDI_G2_Y
[MC_INDI_W_MAX]: ../advanced_config/parameter_reference.md#MC_INDI_W_MAX
[MC_INDI_K_R]: ../advanced_config/parameter_reference.md#MC_INDI_K_R
[MC_INDI_K_P]: ../advanced_config/parameter_reference.md#MC_INDI_K_P
[MC_INDI_K_Y]: ../advanced_config/parameter_reference.md#MC_INDI_K_Y
[MC_INDI_ACT_TC]: ../advanced_config/parameter_reference.md#MC_INDI_ACT_TC
[MC_INDI_LEAD]: ../advanced_config/parameter_reference.md#MC_INDI_LEAD
[MC_INDI_DELAY]: ../advanced_config/parameter_reference.md#MC_INDI_DELAY
[MC_INDI_ERPM_DLY]: ../advanced_config/parameter_reference.md#MC_INDI_ERPM_DLY
[MC_INDI_ERPM_TO]: ../advanced_config/parameter_reference.md#MC_INDI_ERPM_TO
[MC_INDI_ERPM_FRZ]: ../advanced_config/parameter_reference.md#MC_INDI_ERPM_FRZ
[MC_INDI_ACT_BLD]: ../advanced_config/parameter_reference.md#MC_INDI_ACT_BLD
[MC_INDI_DT_MAX]: ../advanced_config/parameter_reference.md#MC_INDI_DT_MAX
[MC_INDI_LND_SLEW]: ../advanced_config/parameter_reference.md#MC_INDI_LND_SLEW
[MC_INDI_SP_TO]: ../advanced_config/parameter_reference.md#MC_INDI_SP_TO
[MC_INDI_YAW_CUT]: ../advanced_config/parameter_reference.md#MC_INDI_YAW_CUT
[MC_INDI_POS_LPF]: ../advanced_config/parameter_reference.md#MC_INDI_POS_LPF
[MC_INDI_POS_DLY]: ../advanced_config/parameter_reference.md#MC_INDI_POS_DLY
[MC_INDI_POS_TB]: ../advanced_config/parameter_reference.md#MC_INDI_POS_TB
[MC_INDI_XY_P]: ../advanced_config/parameter_reference.md#MC_INDI_XY_P
[MC_INDI_XY_VP]: ../advanced_config/parameter_reference.md#MC_INDI_XY_VP
<!-- prettier-ignore-end -->
