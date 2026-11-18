import sys, runpy
sys.path.insert(0, "indi_flight/bench")
import g3_sample
_orig = g3_sample.campaign
start = int(sys.argv[sys.argv.index("--start") + 1])
g3_sample.campaign = lambda s, n: [d for d in _orig(s, n) if d["run_index"] == start]
sys.argv[0] = "indi_flight/bench/g3_run.py"
runpy.run_path("indi_flight/bench/g3_run.py", run_name="__main__")
