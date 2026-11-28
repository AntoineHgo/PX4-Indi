"""G3 campaign (300 runs): per-run outcome, steady-state metric and drawn plant factors (committed files)."""
import csv
import json
import os

import numpy as np

from style import path, read

CAMP = "results/g3_campaign_f10"


def load():
    rows = []
    for r in csv.DictReader(read(CAMP + "/SCORES.tsv").splitlines(), delimiter="\t"):
        i = int(r["idx"])
        d = json.loads(read(f"{CAMP}/run_{i:03d}/g3_draw.json"))["draw"]["factors"]
        k2 = r["key2_failing"].split(",")
        k1 = r["key1_failing"].split(",")
        rec = dict(idx=i, outcome=r["outcome"], key1=r["key1"], key2=r["key2"],
                   item2_any=("item2" in k1) or ("item2" in k2), item2_k1="item2" in k1, item3_k1="item3" in k1,
                   tau=d["tau_scale"]["value"], mass=d["mass_scale"]["value"],
                   delay=d["loop_delay"]["total_ms"], g1=max(abs(np.log(d["g1_err"][a])) for a in ("roll", "pitch", "yaw")),
                   sat=bool(d["saturation"]["on"]), rms=np.nan, tilt=np.nan)
        cp = path(f"{CAMP}/run_{i:03d}/g3_checks.json")
        if os.path.exists(cp):
            c = json.loads(read(f"{CAMP}/run_{i:03d}/g3_checks.json"))
            rec["rms"] = c["item3_steady_state"]["horizontal_rms_m"]["value"]
            rec["tilt"] = c["item1_loc"]["tilt_max_deg"]
        # status: pass / fail (an item failed on key 1) / loc (aborted by the flight watchdog) / other
        if r["key1"] == "pass":
            rec["status"] = "pass"
        elif r["key1"] == "FAIL":
            rec["status"] = "fail"
        elif "tilt" in r["outcome"] or "height" in r["outcome"]:
            rec["status"] = "loc"
        else:
            rec["status"] = "unscored"
        rows.append(rec)
    return rows
