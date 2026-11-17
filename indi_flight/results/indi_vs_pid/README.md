# INDI vs PID inner loop: steps and torque-step disturbance (2026-11-17, ad hoc, not gate-bearing)

Same airframe (quad5in), sim v2 (eRPM telemetry), 800 Hz, seed 1, speed 4. Same attitude P (MC_ROLL/PITCH/YAW_P of
4040_gz_quad5in) and same position loop (stock mc_pos_control, MC_INDI_POS_EN 0); only the rate loop differs.
- INDI: `indi.params` (= S59 hover.params: derived G1/G2, ACT_TC 0.05, LEAD 1, measured rotor W_MAX 2700), K_R/K_P/K_Y default.
- PID: `pid.params` (stock mc_rate_control, airframe tune).

Flights: `fly.sh` (step_roll, step_pitch, step_yaw); torque_steps re-flown by hand with the same command and an absolute
--out (with a relative --out disturbance.py never sees its trigger file and applies nothing: 0 wrench updates).
New scenario `torque_steps` (bench/scenarios.py + disturbance.py profile): 100 mN m roll 0-2 s, 100 mN m pitch 4-6 s,
30 mN m yaw 8-10 s, in position hold. run_scenario.py now passes `--model <model>_0` to the injector (was x500_0 only).

Plots: `python3 plot_compare.py .` -> plots/*.png, metrics.md.
