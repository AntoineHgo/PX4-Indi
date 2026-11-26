"""S241 PID reference flight (speed 1) of one G3 route B campaign index (seed 173 / n 300, campaign of S239).
Usage (repo root):  python3 fly_pid_ref.py IDX [--dry]
Same pattern as results/g3_refly_actc_s212/restore264/ref264_s224/fly_pid_run.py: g3_run.CONTROLLER = pid_default,
base params pid_base.params (no MC_INDI_*), draw asserted equal to the campaign run's g3_draw.json, argv compared with the
campaign INDI command (controller and speed ignored). Output: ref_s241/pid_dIDX/run_IDX. Campaign dir is read only."""
import json, os, subprocess, sys
REPO = "/home/ahugo/Documents/Drotek/Codes/PX4-Indi"
sys.path.insert(0, os.path.join(REPO, "indi_flight", "bench"))
os.chdir(REPO)
import g3_run, g3_sample
IDX = int(sys.argv[1])
DRY = "--dry" in sys.argv[2:]
CAMP = "indi_flight/results/g3_routeB_s239/campaign"
W = "indi_flight/results/g3_routeB_s239/ref_s241"
g3_run.CONTROLLER = "pid_default"
src = json.load(open(f"{CAMP}/run_{IDX:03d}/g3_draw.json"))
d = [x for x in g3_sample.campaign(173, 300) if x["run_index"] == IDX][0]
assert json.dumps(d, sort_keys=True) == json.dumps(src["draw"], sort_keys=True), "draw mismatch vs campaign INDI run"
BASE = "indi_flight/results/g3_pretest_s187/pid_refs/pid_base.params"
out = f"{W}/pid_d{IDX}/run_{IDX:03d}"
r = g3_run.build_run(d, BASE, out)  # speed 1: no --speed in argv
cmd = ["python3", g3_run.RUN_SCENARIO] + r["argv"]


def norm(c, o):
    c = list(c[1:])
    x = []
    i = 0
    while i < len(c):
        if c[i] == "--speed":
            i += 2
            continue
        x.append(c[i].replace(o, "<OUT>"))
        i += 1
    return [a for a in x if a not in ("indi", "pid_default")]


pid = norm(cmd, out)
ind = norm(src["command"], f"{CAMP}/run_{IDX:03d}")
eq = ind == pid
print("CMD", " ".join(cmd), flush=True)
print("ARGV_EQUAL_EXCEPT_CONTROLLER_AND_SPEED vs campaign run", IDX, eq, flush=True)
if not eq:
    print("INDI_ONLY", [a for a in ind if a not in pid], "PID_ONLY", [a for a in pid if a not in ind], flush=True)
print("NOT_APPLIED", r["not_applied"], flush=True)
if DRY:
    sys.exit(0 if eq else 1)
assert eq, "argv mismatch, not flying"
assert not os.path.exists(out), f"{out} exists"
os.makedirs(out)
json.dump({"draw": d, "build": r, "command": cmd, "controller": "pid_default"},
          open(os.path.join(out, "g3_draw.json"), "w"), indent=1, sort_keys=True)
open(os.path.join(out, "g3_params.txt"), "w").write(g3_run.fmt_params(r["merged_params"]))
if r["overrides"]:
    open(os.path.join(out, g3_run.OVERRIDES_NAME), "w").write(json.dumps(r["overrides"], indent=1, sort_keys=True) + "\n")
dock = ["indi_project/docker/run.sh", "-n", f"g3pidS241_{IDX}", "-t", "1500", "--"] + cmd
try:
    with open(os.path.join(out, "g3_stdout.txt"), "w") as so:
        p = subprocess.run(dock, stdout=so, stderr=subprocess.STDOUT, timeout=1550)
    status = {"returncode": p.returncode}
except subprocess.TimeoutExpired:
    status = {"returncode": None, "timeout_s": 1550}
print("STATUS", status, flush=True)
print("OUTCOME", g3_run.finalize(out, status), flush=True)
