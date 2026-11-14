# Stage-2 sim check: rotor speed telemetry from gz (session 27, 2026-11-14)

One flight: `step_roll`, PID defaults, seed 1, speed 1, `--sim v2` (JointStatePublisher on the per-run x500 copy,
`SIM_GZ_ESC_FB=1`). Raw log `s2_escfb_check/step_roll_pid_seed1/flight.ulg` (untracked), `run.json` committed.
Firmware: gz_bridge commit "optional rotor joint speed as ESC rpm feedback".

- Flight OK (`exit_status` ok). `esc_status` at 250 Hz (one per motor command), `esc_rpm` in rpm, 0 before arming.
- Steady state: median motor-0 esc_rpm 7342 vs command 769.0 rad/s = 7344 rpm: unit conversion and the x10
  rotorVelocitySlowdownSim factor are right.
- Dynamics (ad hoc check, all 4 motors, samples with command > 3000 rpm): RMS(esc_rpm - command) 74-104 rpm at lag 0,
  falling with lag (the telemetry lags the command); RMS(esc_rpm - first-order model of the command, tau up 0.0125 s /
  down 0.025 s) 43-84 rpm. So esc_rpm carries the simulated motor lag; it is no longer the command echo. The residual
  to the first-order model (~0.6-1.1 % of hover speed) is not explained here; the step identification of O-3 will
  measure the up/down time constants and delay properly.
- v1 path: `SIM_GZ_ESC_FB=0` (default) executes the old code; the only change on that path is that the node mutex is
  initialised before the first subscription. v1 runs are not re-flown for this.
