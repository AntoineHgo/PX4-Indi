#!/bin/bash
# G3 scoring of every run_NNN in RESULTS_DIR (from S174 score.sh, dir is now an argument): g3_checks.py per run -> g3_checks.json.
# Window (DEVIATION, stand-in scenarios have no 20 s hold): the final "hold" segment (3 s, gust/fault injected at the
# segment before it), [hold_end-3, hold_end] on the ulog base (metrics.json window.end_s = hold end, ulog time).
# Time base: window minus ulog start_timestamp (first attempt without it landed after touchdown).
# Flags: --wind for position runs with wind/gust (every o1 run has gust_x); --sag if sag, weak motor or saturation on;
# --mode position for o1_lemniscate, attitude for stick runs (acro: roll/pitch gate not defined, UNVERIFIED).
# needs scipy: run inside Docker, see bench/g3_score_docker.sh
D=$(cd "${1:?usage: g3_score.sh RESULTS_DIR (holds run_NNN/)}" && pwd); B=$(cd "$(dirname "$0")" && pwd)
for r in "$D"/run_*; do
  args=$(python3 - "$r" <<'PY'
import json, sys
r = sys.argv[1]
run = json.load(open(r + "/run.json")); m = json.load(open(r + "/metrics.json"))
f = json.load(open(r + "/g3_draw.json"))["draw"]["factors"]
ev = {e["name"]: e for e in run["events"]}
from pyulog import ULog
st = ULog(r + "/flight.ulg", message_name_filter_list=["vehicle_status"]).start_timestamp / 1e6
# metrics.json window is on the px4 clock; g3_checks.py uses seconds since ulog start_timestamp
t1 = m["window"]["end_s"] - st; t0 = t1 - ev["hold"]["dur_s"]
pos = run["scenario"] == "o1_lemniscate"
a = f"--t0 {t0:.3f} --t1 {t1:.3f} --mode {'position' if pos else 'attitude'}"
if pos and (f["wind"]["steady_ms"] > 0 or f["wind"]["gust_amp_ms"] > 0): a += " --wind"
if any(f[k]["on"] for k in ("thrust_sag", "weak_motor", "saturation")): a += " --sag"
print(a)
PY
)
  echo "$(basename "$r") $args"
  python3 "$B/g3_checks.py" "$r/flight.ulg" $args --json "$r/g3_checks.json" > "$r/g3_checks.txt" 2>&1
done
