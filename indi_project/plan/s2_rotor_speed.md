# Stage 2, step 2a: real rotor speed out of gz (session 26, design note, no code yet)

## What happens today (verified in this repo)

- `GZMixingInterfaceESC` advertises `gz::msgs::Actuators` on `/<model>/command/motor_speed`
  (`src/modules/simulation/gz_bridge/GZMixingInterfaceESC.cpp:49-50`) and subscribes to the **same topic**
  (`:41-43`). `motorSpeedCallback` copies `actuators.velocity(i)` into `esc_status.esc[i].esc_rpm` (`:132`).
  So `esc_rpm` is PX4's own motor command echoed back: no motor dynamics, and the unit is the command unit
  (rad/s of the gz motor model, not rpm).
- `Tools/simulation/gz/models/x500/model.sdf`: four `gz::sim::systems::MulticopterMotorModel` plugins,
  `motorType velocity`, `timeConstantUp 0.0125`, `timeConstantDown 0.025`, `maxRotVelocity 1000`,
  `rotorVelocitySlowdownSim 10`, `commandSubTopic command/motor_speed`. No `JointStatePublisher` in the model
  or in the default world.

## Proposed change (simulator commit, applied identically to both controllers)

1. Add `gz::sim::systems::JointStatePublisher` for `rotor_0_joint..rotor_3_joint` in a **new model variant**
   (e.g. `x500_rpm`, `<include>` of x500 + the plugin) so the v1 configuration `gz_x500` stays reproducible.
2. In GZBridge, behind a new parameter (e.g. `SIM_GZ_ESC_FB`: 0 = echo command (v1, default), 1 = joint
   state), subscribe to the joint-state topic and publish `esc_status.esc[i].esc_rpm` from the joint velocity
   times `rotorVelocitySlowdownSim` (10), converted rad/s -> rpm (x 60 / 2 pi), so the unit matches what the
   DShot driver publishes on hardware.
3. The eRPM telemetry model (rate, latency, quantisation, dropouts; values from
   `research/notes/am32_erpm.md`) sits between that true speed and `esc_status`, as a separate commit.

## To verify before coding (from gz-sim source, not done yet)

- That `MulticopterMotorModel` in velocity mode sets the joint velocity to the first-order-filtered speed
  divided by `rotorVelocitySlowdownSim` (so joint velocity x 10 is the simulated motor speed, with at most
  one physics step of lag).
- Whether the velocity command reaches the parent link as a reaction torque (needed for O-4/G2 as well).
- The joint-state topic name (`/world/<world>/model/<model>/joint_state`) and its publish rate (must be
  at least the PX4 loop rate; check the plugin's `update_rate` option).
