"""Re-draw seed 173 n 300 idx 0-19 with the current sampler; write draw table and diff vs freeze-10 g3_draw.json (draw + build.argv)."""
import json, sys, os
sys.path.insert(0, "indi_flight/bench")
import g3_sample, g3_run
OLD = "indi_flight/results/freeze10_s193/g3_pretest"
NEW = "indi_flight/results/g3_pretest_q24_s197"
BASE = "indi_flight/results/g5_freeze_s157/params.params"
def flat(d, p=""):
    o = {}
    if isinstance(d, dict):
        for k, v in d.items(): o.update(flat(v, p + k + "."))
    elif isinstance(d, list):
        for i, v in enumerate(d): o.update(flat(v, p + str(i) + "."))
    else: o[p[:-1]] = d
    return o
draws = [d for d in g3_sample.campaign(173, 300) if d["run_index"] < 20]
table, changed = {}, []
for d in draws:
    i = d["run_index"]
    old = json.load(open(f"{OLD}/run_{i:03d}/g3_draw.json"))
    nb = g3_run.build_run(d, BASE, f"{NEW}/run_{i:03d}")
    fo, fn = flat(old["draw"]), flat(d)
    diffs = {k: (fo.get(k), fn.get(k)) for k in set(fo) | set(fn) if fo.get(k) != fn.get(k)}
    ao, an = flat(old["build"]["applied"]), flat(nb["applied"])
    ad = {k: (ao.get(k), an.get(k)) for k in set(ao) | set(an) if ao.get(k) != an.get(k)}
    vo, vn = old["command"], g3_run.command(nb["argv"])
    cd = [(a, b) for a, b in zip(vo, vn) if a != b]
    po = open(f"{OLD}/run_{i:03d}/g3_params.txt").read(); pn = g3_run.fmt_params(nb["merged_params"])
    table[i] = {"draw_diff": diffs, "applied_diff": ad, "argv_diff": cd, "argv_len_eq": len(vo) == len(vn), "params_equal": po == pn,
                "latency": fn.get("factors.gnss.latency_ms"), "ekf_old": fo.get("factors.gnss.ekf_delay_ms"), "ekf_new": fn.get("factors.gnss.ekf_delay_ms"),
                "matched": fn.get("factors.gnss.matched")}
    if diffs: changed.append(i)
json.dump(table, open(f"{NEW}/draw_diff.json", "w"), indent=1, sort_keys=True)
for i, t in table.items():
    print(i, "lat", t["latency"], "ekf", t["ekf_old"], "->", t["ekf_new"], "matched", t["matched"], "| draw keys changed:", sorted(t["draw_diff"]), "| applied:", sorted(t["applied_diff"]), "| argv:", t["argv_diff"], "| params_eq", t["params_equal"], t["argv_len_eq"])
print("CHANGED", changed)
