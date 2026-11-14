# T8 motor_loss_0 log

## Step 1: mechanism verification (source)
- 4001_gz_x500 sets SIM_GZ_EC_FUNC1..4 = 101..104 (Motor 1..4), MIN=150, MAX=1000. PX4 motor 0 (0-indexed, actuator_motors control[0])
  = Motor 1 = channel param index 1: SIM_GZ_EC_MIN1 / SIM_GZ_EC_MAX1.
- Mapping in MixingOutput (src/lib/mixer_module/mixer_module.cpp): output = interpolate(value, -1..1 -> min..max), i.e. omega = MIN + (MAX-MIN)*c.
  So scaling MAX alone is NOT a pure thrust scale (omega = 150 + (0.837*1000-150) c). To get thrust x0.7 at every command, scale BOTH MIN1 and MAX1
  by sqrt(0.7)=0.83666 (int params -> 126 / 837, thrust ratio 0.7006).
- Runtime pickup: GZBridge::ScheduledRun handles parameter_update and calls _mixing_interface_esc.updateParams() -> MixingOutput::updateParams()
  re-reads min/max param handles into _min_value/_max_value. Verified in source (GZBridge.cpp:188-197, mixer_module.cpp:153-190). OK.
- Runner already has sim.set_param (px4-param CLI on the instance, notifies parameter_update); using it rather than raw MAVLink PARAM_SET (same effect).

## Step 2: implementation
- scenarios.py: `motor_loss_0` (attitude mode, yaw axis): settle 5 s, loss 10 s (event at start), yaw +45 deg 4 s, zero 4 s; key `motor_fault`.
- run_scenario.py: get_param via `px4-param show -q`; at start of segment "loss" scales MIN1 and MAX1 by sqrt(0.7); run.json["motor_fault"]
  {nominal, applied, event_us, ...}.
- metrics.py: metrics.json["motor_fault"] (post-event tilt error RMS/peak vs setpoint, saturation time, motor means).

## Step 3: test flight (pid_default, seed 1, speed 1, NAME_TAG=t8) -> results/runs/motor_loss_0/pid_default/seed1
- Event at ULog t=40.428 s; param set MIN1 150->125, MAX1 1000->837 (px4-param CLI), nominal read at start. No error, exit ok.
- actuator_motors mean control before event (-3..0 s): [0.728 0.728 0.728 0.728].
  1..10 s after: [0.905 0.732 0.730 0.730]; 11..15 s after (yaw step): [0.866 0.698 0.744 0.745].
  Motor 0 needs ~0.905 to reach the same omega (~770 rad/s) as the others at 0.73 -> the mapping change is effective (thrust x0.7 per command),
  controller compensates fully. Vehicle stayed airborne: z (NED) -4.99 before -> -3.89 at +9 s -> -3.74 at +17 s (about 1.2 m sag, altitude PD).
- metrics.json["motor_fault"]: attitude_rms 1.10 deg, peak tilt error 5.12 deg, saturation_time 1.73 s (faulty motor >=0.99: 1.54 s),
  motor mean faulty 0.90 vs others 0.725.
- Not done: MIN/MAX are int params so thrust ratio is 0.7006 (not exact 0.7); gz motor model dynamics (time constants) unchanged.
