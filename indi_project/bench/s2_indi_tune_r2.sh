#!/usr/bin/env bash
# v2 INDI tuning round 2: 16 candidates x 3 seeds centred on the r1 best (lowest J with no failure), same budget
# rule, sampler seed and span as the v2 PID r2f (bench/s2_pid_tune_r2f.sh). Waits for r1 (s2_indi_tune_r1.sh).
cd /home/ahugo/Documents/Drotek/Codes/PX4-Indi
P=/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_project
while pgrep -f 's2_indi_tune_r1.sh|--family indi --round-name r1 ' > /dev/null; do sleep 60; done
C=$P/bench/params/indi_v2_r1_best.json
python3 - "$P/results/s2_tuning/indi/r1/summary.csv" "$C" <<'PY' || exit 1
import csv, json, sys
rows = [r for r in csv.DictReader(open(sys.argv[1])) if int(r["failures"]) == 0]
best = min(rows, key=lambda r: float(r["J"]))
keep = ("MC_INDI_K_R", "MC_INDI_K_P", "MC_INDI_K_Y", "MC_INDI_YAW_CUT", "MC_ROLL_P", "MC_PITCH_P", "MC_YAW_P")
json.dump({"cand": best["cand"], "J": float(best["J"]), "params": {k: float(best[k]) for k in keep}}, open(sys.argv[2], "w"))
print("[r2] centre", best["cand"], best["J"])
PY
export SIM_VERSION=v2 IMU_RATE=1000 ERPM_DROP=0.01 VIB_ACC=1.0 VIB_GYR=0.05
export TUNE_REF_ROOT=$P/results/s2_tuning/ref_fac TUNE_REF_PARAMS=$P/bench/params/v2_fac.params TUNE_OUT_ROOT=$P/results/s2_tuning
exec timeout 14400 python3 indi_project/bench/tune.py --family indi --round-name r2 --n-candidates 16 --seeds 1 2 3 \
	--jobs 6 --sampler-seed 1 --span-factor 1.5 --base-params indi_project/bench/params/indi_v2_start.params \
	--center $C --vary MC_INDI_K_R MC_INDI_K_P MC_INDI_K_Y MC_INDI_YAW_CUT MC_ROLL_P MC_PITCH_P MC_YAW_P
