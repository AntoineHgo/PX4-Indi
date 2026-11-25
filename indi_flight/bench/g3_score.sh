#!/bin/bash
# G3 scoring of every run_NNN in RESULTS_DIR (from S174 score.sh, dir is now an argument): g3_checks.py per run -> g3_checks.json.
# Window (S214, Q30 B): runs of the dedicated G3 scenarios (g3_lemniscate / g3_stick_zsine, `hold` event >= 20 s) are scored with
# g3_checks.py --run-json run.json: item 3 = last 10 s of the hold, item 6 (acro) = last 20 s, items 4-5 and the S225 item-2 fault/gust
# window skip from the run.json events (times t_us minus the ulog start_timestamp).
# Old runs (stand-in scenarios, `hold` event < 20 s) keep the pre-S214 3 s stand-in window (re-scoring old results):
# the final "hold" segment, [hold_end-3, hold_end] on the ulog base (metrics.json window.end_s = hold end, ulog time).
# Time base: window minus ulog start_timestamp (first attempt without it landed after touchdown).
# Flags: --wind for position runs with wind/gust (every o1 run has gust_x); --sag if sag, weak motor or saturation on;
# --mode position for o1_lemniscate, attitude for stick runs (acro: roll/pitch gate not defined, UNVERIFIED).
# needs scipy: run inside Docker, see bench/g3_score_docker.sh
D=$(cd "${1:?usage: g3_score.sh RESULTS_DIR (holds run_NNN/)}" && pwd); B=$(cd "$(dirname "$0")" && pwd)
# Q27 item 8: a harness-aborted run (g3_run_status.py) is INVALID (re-fly), never scored: g3_checks.json {"invalid": true, "pass": null}.
# Q27 item 6 (S208): key 1 always passes --skip-nav-change to g3_checks.py (item 2 skips windows within 3 s after a nav_state change).
for r in "$D"/run_*; do
  if bad=$(python3 "$B/g3_run_status.py" "$r"); then :; else
    echo "$(basename "$r") $bad"
    printf '{"invalid": true, "invalid_reason": %s, "pass": null}\n' "$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$bad")" > "$r/g3_checks.json"
    echo "$bad" > "$r/g3_checks.txt"
    continue
  fi
  args=$(python3 - "$r" <<'PY'
import json, sys
r = sys.argv[1]
run = json.load(open(r + "/run.json")); m = json.load(open(r + "/metrics.json"))
f = json.load(open(r + "/g3_draw.json"))["draw"]["factors"]
ev = {e["name"]: e for e in run["events"]}
from pyulog import ULog
st = ULog(r + "/flight.ulg", message_name_filter_list=["vehicle_status"]).start_timestamp / 1e6
pos = run["scenario"] in ("o1_lemniscate", "g3_lemniscate")
if ev["hold"]["dur_s"] >= 20.0:   # S214 window from run.json (key 1 derives it itself)
    a = f"--run-json {r}/run.json --mode {'position' if pos else 'attitude'}"
    if json.load(open(r + "/g3_draw.json"))["draw"]["mode"] == "acro":
        a += " --rate-mode"
else:
    # metrics.json window is on the px4 clock; g3_checks.py uses seconds since ulog start_timestamp
    t1 = m["window"]["end_s"] - st; t0 = t1 - ev["hold"]["dur_s"]
    a = f"--t0 {t0:.3f} --t1 {t1:.3f} --mode {'position' if pos else 'attitude'}"
if pos and (f["wind"]["steady_ms"] > 0 or f["wind"]["gust_amp_ms"] > 0): a += " --wind"
if any(f[k]["on"] for k in ("thrust_sag", "weak_motor", "saturation")): a += " --sag"
print(a)
PY
)
  echo "$(basename "$r") $args"
  python3 "$B/g3_checks.py" "$r/flight.ulg" $args --skip-nav-change --json "$r/g3_checks.json" > "$r/g3_checks.txt" 2>&1
done
