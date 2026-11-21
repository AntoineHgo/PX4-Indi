"""G3 pre-test PID reference flight of one INDI run (same seed 173 / n 300 draw). Usage (repo root, inside docker via fly_all_pid.sh):
   python3 fly_pid_run.py IDX [--dry]
Derived from g3_pretest_s173/run_017_pid_s185/fly_pid_run017.py; index parametrised, INDI draw taken from g3_pretest_s187/run_NNN/g3_draw.json.
Output: g3_pretest_s187/pid_refs/run_NNN (same layout as the INDI runs so g3_score.sh / g3_score_docker.sh work on pid_refs/).
--dry: build and print the command, compare with the INDI run's command, do not fly. Host python needs no docker; the flight itself is run
via indi_project/docker/run.sh (name g3pid188_NNN, -t 1000, subprocess timeout 1100)."""
import json, os, subprocess, sys
REPO = "/home/ahugo/Documents/Drotek/Codes/PX4-Indi"
sys.path.insert(0, os.path.join(REPO, "indi_flight", "bench"))
os.chdir(REPO)
import g3_run, g3_sample
IDX = int(sys.argv[1])
DRY = "--dry" in sys.argv[2:]
R = "indi_flight/results/g3_pretest_s187"
CTRL = "pid_default"
g3_run.CONTROLLER = CTRL  # build_run: no MC_RATE_CTL_TYPE, argv --controller pid_default; check_validity uses pid (run_validity pid_* alias)
src = json.load(open(f"{R}/run_{IDX:03d}/g3_draw.json"))
draws = g3_sample.campaign(173, 300)
d = [x for x in draws if x["run_index"] == IDX][0]
assert json.dumps(d, sort_keys=True) == json.dumps(src["draw"], sort_keys=True), "draw mismatch vs INDI run"
BASE = f"{R}/pid_refs/pid_base.params"
out = f"{R}/pid_refs/run_{IDX:03d}"
r = g3_run.build_run(d, BASE, out)
cmd = ["python3", g3_run.RUN_SCENARIO] + r["argv"]
# compare with the INDI command: only controller, out dir and params path may differ
def norm(c, o):
    return [a.replace(o, "<OUT>") for a in c[1:] if a not in ("indi", "pid_default")]
ind = norm(src["command"], f"{R}/run_{IDX:03d}")
pid = norm(cmd, out)
print("CMD", " ".join(cmd), flush=True)
print("ARGV_EQUAL_EXCEPT_CONTROLLER", ind == pid, flush=True)
if ind != pid:
    print("INDI_ONLY", [a for a in ind if a not in pid], "PID_ONLY", [a for a in pid if a not in ind], flush=True)
if DRY:
    sys.exit(0)
assert not os.path.exists(out), f"{out} exists"
os.makedirs(out)
json.dump({"draw": d, "build": r, "command": cmd, "controller": CTRL}, open(os.path.join(out, "g3_draw.json"), "w"), indent=1, sort_keys=True)
open(os.path.join(out, "g3_params.txt"), "w").write(g3_run.fmt_params(r["merged_params"]))
if r["overrides"]:
    open(os.path.join(out, g3_run.OVERRIDES_NAME), "w").write(json.dumps(r["overrides"], indent=1, sort_keys=True) + "\n")
print("NOT_APPLIED", r["not_applied"], flush=True)
dock = ["indi_project/docker/run.sh", "-n", f"g3pid188_{IDX}", "-t", "1000", "--"] + cmd
try:
    with open(os.path.join(out, "g3_stdout.txt"), "w") as so:
        p = subprocess.run(dock, stdout=so, stderr=subprocess.STDOUT, timeout=1100)
    status = {"returncode": p.returncode}
except subprocess.TimeoutExpired:
    status = {"returncode": None, "timeout_s": 1100}
print("STATUS", status, flush=True)
print("OUTCOME", g3_run.finalize(out, status), flush=True)
