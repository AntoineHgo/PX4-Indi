# per-cell scenario copy: hover plus sim_params SIM_GZ_ERPM_LAT=3 (PX4_PARAM_ env at boot), then the stock run_scenario.py
import os, runpy, sys
BENCH = '/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/bench'
sys.path.insert(0, BENCH)
import scenarios
scenarios.SCENARIOS["hover_lat3"] = {**scenarios.SCENARIOS["hover"], "sim_params": {"SIM_GZ_ERPM_LAT": 3}}
sys.argv[0] = os.path.join(BENCH, "run_scenario.py")
runpy.run_path(sys.argv[0], run_name="__main__")
