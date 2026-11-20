#!/usr/bin/env bash
# per-run json + summary txt from the logs (run from repo root)
cd "$(dirname "$0")/../../.."; D=indi_flight/results/g5_g55_s139
for r in $D/*_s[123]; do [ -f $r/flight.ulg ] && { python3 indi_flight/bench/g55_check.py $r --json $r.json >/dev/null; }; done
python3 - <<'P' > $D/summary.txt
import json,glob
for f in sorted([x for x in glob.glob("indi_flight/results/g5_g55_s139/*_s[123].json") if "scenario" in open(x).read()]):
    j=json.load(open(f))
    keys=[k for k in ("rms_h_m","rms_v_m","vx_rms_last3s","vx_end_abs","dz_max") if k in j]
    print(j["scenario"],j["seed"],j["verdict"]," ".join("%s=%.3f"%(k,j[k]) for k in keys),j["invalid"] or "")
P
cat $D/summary.txt
