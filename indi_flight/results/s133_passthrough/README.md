# S133 pass-through / offboard-velocity probes (quad5in, seed 1, speed 4, sim v2, params.params = S131 file with MC_INDI_POS_EN 1)
Commands (inside docker, serial):
  indi_project/docker/run.sh -n s133acro -t 800 -- python3 indi_flight/bench/run_scenario.py --scenario stick_zsine_o6 --stick-mode acro --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --params indi_flight/results/s133_passthrough/params.params --out indi_flight/results/s133_passthrough/acro
  same with --scenario offb_vel_step (no --stick-mode) --out .../vel
Checks: bench/passthrough_check.py, bench/offb_vel_check.py, bench/t9_step_check.py on <run>/flight.ulg.
Metrics: see indi_flight/design/impl_s133_offboard_passthrough.md (ACRO: 0 att_sp while flags off; vel: last-3 s vx RMS 0.092 m/s, z max dev 0.040 m; T9: vel 1.03 %, acro 6.12 %).
