"""G3 S199 PID reference flight (speed 1) of one campaign index (seed 173 / n 300). Usage (repo root):
   python3 fly_pid_run.py IDX [--dry]
Adapted from g3_pretest_s187/pid_refs/fly_pid_run.py. Draw is asserted equal to indi_flight/results/g3_campaign_f10/run_NNN/g3_draw.json
(the speed-4 campaign INDI run). Argv equality (controller and --speed ignored) is checked against the campaign run and, when it exists,
against the speed-1 INDI re-fly g3_refly_actc_s212/speed1_s213/indi_NNN/run_NNN (there --speed is absent too, so that check is strict except controller).
Output: q31_injector_fix_s214/pid_NNN/run_NNN (S214 copy: fixed gz_bridge binary, Q31 verification)."""
import json, os, subprocess, sys
REPO = "/home/ahugo/Documents/Drotek/Codes/PX4-Indi"
sys.path.insert(0, os.path.join(REPO, "indi_flight", "bench"))
os.chdir(REPO)
import g3_run, g3_sample
IDX = int(sys.argv[1])
DRY = "--dry" in sys.argv[2:]
CAMP = "indi_flight/results/g3_refly_actc_s212"
W = "indi_flight/results/q31_injector_fix_s214"
SAMPLES = CAMP + "/samples"
g3_run.CONTROLLER = "pid_default"
src = json.load(open(f"{CAMP}/run_{IDX:03d}/g3_draw.json"))
d = [x for x in g3_sample.load_samples(SAMPLES, 173, 300) if x["run_index"] == IDX][0]
assert json.dumps(d, sort_keys=True) == json.dumps(src["draw"], sort_keys=True), "draw mismatch vs campaign INDI run"
BASE = "indi_flight/results/g3_pretest_s187/pid_refs/pid_base.params"
out = f"{W}/pid_{IDX:03d}/run_{IDX:03d}"
r = g3_run.build_run(d, BASE, out)  # speed 1: no --speed in argv
cmd = ["python3", g3_run.RUN_SCENARIO] + r["argv"]
def norm(c, o):
    c = list(c[1:]); x = []
    i = 0
    while i < len(c):
        if c[i] == "--speed": i += 2; continue
        x.append(c[i].replace(o, "<OUT>")); i += 1
    return [a for a in x if a not in ("indi", "pid_default")]
pid = norm(cmd, out)
ok_all = True
ref = [(f"chain C212 speed-4 run_{IDX:03d}", src["command"], f"{CAMP}/run_{IDX:03d}")]
p1 = f"{W}/indi_{IDX:03d}/run_{IDX:03d}/g3_draw.json"
if os.path.exists(p1):
    ref.append(("speed-1 INDI re-fly", json.load(open(p1))["command"], f"{W}/indi_{IDX:03d}/run_{IDX:03d}"))
print("CMD", " ".join(cmd), flush=True)
for name, c, o in ref:
    ind = norm(c, o)
    eq = ind == pid
    ok_all &= eq
    print("ARGV_EQUAL_EXCEPT_CONTROLLER_AND_SPEED vs", name, eq, flush=True)
    if not eq:
        print("INDI_ONLY", [a for a in ind if a not in pid], "PID_ONLY", [a for a in pid if a not in ind], flush=True)
if DRY:
    sys.exit(0 if ok_all else 1)
assert ok_all, "argv mismatch, not flying"
assert not os.path.exists(out), f"{out} exists"
os.makedirs(out)
json.dump({"draw": d, "build": r, "command": cmd, "controller": "pid_default"}, open(os.path.join(out, "g3_draw.json"), "w"), indent=1, sort_keys=True)
open(os.path.join(out, "g3_params.txt"), "w").write(g3_run.fmt_params(r["merged_params"]))
if r["overrides"]:
    open(os.path.join(out, g3_run.OVERRIDES_NAME), "w").write(json.dumps(r["overrides"], indent=1, sort_keys=True) + "\n")
print("NOT_APPLIED", r["not_applied"], flush=True)
dock = ["indi_project/docker/run.sh", "-n", f"q31pid214_{IDX}", "-t", "1000", "--"] + cmd
try:
    with open(os.path.join(out, "g3_stdout.txt"), "w") as so:
        p = subprocess.run(dock, stdout=so, stderr=subprocess.STDOUT, timeout=1100)
    status = {"returncode": p.returncode}
except subprocess.TimeoutExpired:
    status = {"returncode": None, "timeout_s": 1100}
print("STATUS", status, flush=True)
print("OUTCOME", g3_run.finalize(out, status), flush=True)
