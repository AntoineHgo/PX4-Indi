import json, os, subprocess, sys
REPO = "/home/ahugo/Documents/Drotek/Codes/PX4-Indi"
sys.path.insert(0, os.path.join(REPO, "indi_flight", "bench"))
os.chdir(REPO)
import g3_run, g3_sample
CTRL = "pid_default"
g3_run.CONTROLLER = CTRL  # build_run: no MC_RATE_CTL_TYPE, argv --controller pid_default, check_validity uses pid
src = json.load(open("indi_flight/results/g3_pretest_s173/run_017/g3_draw.json"))["draw"]
draws = g3_sample.campaign(173, 300)
d = [x for x in draws if x["run_index"] == 17][0]
assert json.dumps(d, sort_keys=True) == json.dumps(src, sort_keys=True), "draw mismatch"
BASE = os.path.join(sys.argv[1], "pid_base.params")
out = "indi_flight/results/g3_pretest_s173/run_017_pid_s185"
assert not os.path.exists(out)
r = g3_run.build_run(d, BASE, out)
cmd = ["python3", g3_run.RUN_SCENARIO] + r["argv"]
os.makedirs(out)
json.dump({"draw": d, "build": r, "command": cmd, "controller": CTRL}, open(os.path.join(out, "g3_draw.json"), "w"), indent=1, sort_keys=True)
open(os.path.join(out, "g3_params.txt"), "w").write(g3_run.fmt_params(r["merged_params"]))
if r["overrides"]:
    open(os.path.join(out, g3_run.OVERRIDES_NAME), "w").write(json.dumps(r["overrides"], indent=1, sort_keys=True) + "\n")
print("NOT_APPLIED", r["not_applied"], flush=True)
print("CMD", " ".join(cmd), flush=True)
dock = ["indi_project/docker/run.sh", "-n", "pid173_17", "-t", "1000", "--"] + cmd
try:
    with open(os.path.join(out, "g3_stdout.txt"), "w") as so:
        p = subprocess.run(dock, stdout=so, stderr=subprocess.STDOUT, timeout=1100)
    status = {"returncode": p.returncode}
except subprocess.TimeoutExpired:
    status = {"returncode": None, "timeout_s": 1100}
print("STATUS", status, flush=True)
print("OUTCOME", g3_run.finalize(out, status), flush=True)
