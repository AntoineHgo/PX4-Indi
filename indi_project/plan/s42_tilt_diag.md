# Session 42 diagnosis brief: steady tilt of indi_v2 in held-out V motor_loss_0

## Observation (orchestrator, session 42)

Logs: `indi_project/results/s2_heldout_v2/runs/motor_loss_0/{indi_v2,pid_tuned,pid_default}/seed{1,2,4..10}/`
(`flight.ulg`, `run.json` with segment events, `runner.log`, `px4.log`). Scenario `motor_loss_0`
(`bench/scenarios.py`): offboard attitude mode, segments settle 37 s, loss 42 s (motor 0 SIM_GZ_EC_MIN/MAX scaled
by sqrt(0.7)), up 52 s, zero 56 s, sim v2, speed 1.

indi_v2, seeds 1 and 2: from about t = 27 s the vehicle holds a steady diagonal tilt (roll +9.4 deg, pitch -9.4 deg,
std 0.05 deg over 2 s) while `vehicle_attitude_setpoint` is level, and drifts about 160 m in x by t = 45 s. It ends
at z = 0.1 m from 55 s (as PID, which lands). pid_tuned stays level (error < 0.1 deg) over the same span. The tilt
starts well BEFORE the motor fault. Other V entries flown at speed 1 (com_shift, gust_diag) do not show a large INDI
attitude error in their metrics.

## Question

Why does the INDI rate loop (module `src/modules/mc_indi_rate_control`, law in `src/lib/indi_rate_control`) not
remove a steady 9 deg attitude error in this run? Is it a controller/integration defect, a runner or scenario
artefact (e.g. a mode switch, a parameter set by the runner around t = 25-30 s, the nominal SIM_GZ_EC read), or a
real property of the tuned law (`bench/params/indi_v2_tuned.params`)?

## Method (keep to about 30 tool calls)

1. From `runner.log`, `px4.log` and run.json find what happens at t = 20-30 s (mode switches, param sets).
2. With pyulog (run with `python3 -I`), over t = 20-45 s on indi_v2 seed 2, extract in 1 s bins: rate setpoint vs
   rate (`vehicle_rates_setpoint`, `vehicle_angular_velocity`), torque setpoint (`vehicle_torque_setpoint`, and which
   module publishes it if both instances exist), the INDI status topic (find its name in `msg/`), motor outputs
   (`actuator_motors`), eRPM (`esc_status`), `vehicle_control_mode` flags, `actuator_controls_status` /
   allocator saturation flags (`control_allocator_status`). Do the same for pid_tuned seed 2 for comparison.
3. Check whether the same tilt exists in the other indi_v2 seeds (one number per seed: mean |roll err| over 30-40 s)
   and in `indi_project/results/s2_seen_v2/runs/*/indi_v2/seed1` entries that have a `flight.ulg` already.
4. Read the relevant code path only as far as needed to explain the signals.

## Output

Write `indi_project/results/s2_tilt_diag.md` after EACH step (numbers, topics used, the script you used saved as
`indi_project/bench/tilt_diag.py`). End with: the cause if found, evidence for it, and anything unverified flagged.
Do not change firmware, do not fly simulations, do not touch running Docker containers (a batch is flying), do not
commit. Return a summary of at most 10 lines.
