# S60 hover slice (T122)
Flight: `indi_project/docker/run.sh -n s60hov -t 420 -- python3 indi_flight/bench/run_scenario.py --scenario hover --controller indi_s60 --model quad5in --seed 1 --speed 4 --params indi_flight/results/stage5_s60/hover_slice/hover.params --out indi_flight/results/stage5_s60/hover_slice/run` (rc 0, exit_status ok)
Gate: `python3 indi_flight/bench/pretest_gate.py run/flight.ulg gate.md` -> PASS (rate RMS 0.0028/0.0028/0.0004, pin 0, achieved 1.0)
hover.params = MC_RATE_CTL_TYPE 1, SENS_BAR_AUTOCAL 0, MC_INDI_ACT_TC 0.05, MC_INDI_LEAD 1, MC_INDI_POS_EN 1 (G1/G2 come from the airframe file quad5in_indi_g1.params, applied by run_scenario).
