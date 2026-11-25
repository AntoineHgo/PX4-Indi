"""G3 pretest S227 PID reference: stock PID (pid_default, pid_base.params from S188) on the S227 INDI draw (seed 173, index 0).
Usage (repo root): python3 indi_flight/results/g3_pretest_s230/pid_ref/fly_pid_s227.py [--dry]
Adapted from g3_refly_s199/fly_pid_run.py. Output: g3_pretest_s230/pid_ref/run_000."""
import hashlib, json, os, subprocess, sys
REPO = "/home/ahugo/Documents/Drotek/Codes/PX4-Indi"
sys.path.insert(0, os.path.join(REPO, "indi_flight", "bench"))
os.chdir(REPO)
import g3_run, g3_sample
DRY = "--dry" in sys.argv[1:]
IDX = 0
S = "indi_flight/results/g3_pretest_s230"
INDI = f"{S}/indi_d0/run_000"
OUT = f"{S}/pid_d0/run_000"
BIN = "build/px4_sitl_default/bin/px4"
PINNED = "903eae63ceb1bf019215076650cf02fb38cac8534618530410506f6a505f6d62"
sha = hashlib.sha256(open(BIN, "rb").read()).hexdigest()
print("BINARY", sha[:12], "match" if sha == PINNED else "MISMATCH", flush=True)
assert sha == PINNED, "binary is not the pinned 903eae63"
g3_run.CONTROLLER = "pid_default"
src = json.load(open(f"{INDI}/g3_draw.json"))
d = [x for x in g3_sample.campaign(173, 300) if x["run_index"] == IDX][0]
assert json.dumps(d, sort_keys=True) == json.dumps(src["draw"], sort_keys=True), "draw mismatch vs S227 INDI run"
BASE = "indi_flight/results/g3_pretest_s187/pid_refs/pid_base.params"
r = g3_run.build_run(d, BASE, OUT)
cmd = ["python3", g3_run.RUN_SCENARIO] + r["argv"]
def norm(c, o):
    c = list(c[1:]); x = []; i = 0
    while i < len(c):
        if c[i] == "--speed": i += 2; continue
        x.append(c[i].replace(o, "<OUT>")); i += 1
    return [a for a in x if a not in ("indi", "pid_default")]
eq = norm(src["command"], INDI) == norm(cmd, OUT)
print("ARGV_EQUAL_EXCEPT_CONTROLLER", eq, flush=True)
print("CMD", " ".join(cmd), flush=True)
if DRY:
    sys.exit(0 if eq else 1)
assert eq, "argv mismatch, not flying"
assert not os.path.exists(OUT), f"{OUT} exists"
os.makedirs(OUT)
json.dump({"draw": d, "build": r, "command": cmd, "controller": "pid_default"}, open(os.path.join(OUT, "g3_draw.json"), "w"), indent=1, sort_keys=True)
open(os.path.join(OUT, "g3_params.txt"), "w").write(g3_run.fmt_params(r["merged_params"]))
if r["overrides"]:
    open(os.path.join(OUT, g3_run.OVERRIDES_NAME), "w").write(json.dumps(r["overrides"], indent=1, sort_keys=True) + "\n")
print("NOT_APPLIED", r["not_applied"], flush=True)
dock = ["indi_project/docker/run.sh", "-n", "g3pidS230_0", "-t", "1000", "--"] + cmd
try:
    with open(os.path.join(OUT, "g3_stdout.txt"), "w") as so:
        p = subprocess.run(dock, stdout=so, stderr=subprocess.STDOUT, timeout=1100)
    status = {"returncode": p.returncode}
except subprocess.TimeoutExpired:
    status = {"returncode": None, "timeout_s": 1100}
print("STATUS", status, flush=True)
print("OUTCOME", g3_run.finalize(OUT, status), flush=True)
