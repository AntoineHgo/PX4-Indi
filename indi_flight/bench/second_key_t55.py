#!/usr/bin/env python3
"""Second-key checks of the T55 pretest flights (session 26).

Run through the docker wrapper (pyulog is only in the image):
  bash indi_project/docker/run.sh -n sk55 -t 900 -- python3 indi_flight/bench/second_key_t55.py

Writes per-row CSVs to indi_flight/results/second_key_t55_s26/ and prints tables.
"""
import csv
import json
import os
from collections import Counter

import numpy as np
from pyulog import ULog

REPO = "/home/ahugo/Documents/Drotek/Codes/PX4-Indi"
RES = os.path.join(REPO, "indi_flight/results/t55_pretest_s26")
OUT = os.path.join(REPO, "indi_flight/results/second_key_t55_s26")
TOL_US = 1250
KIND_CODE = {"arm": 1, "mode_offboard": 3, "sp_back": 11, "anchor": 6, "sp_hold": 5, "att": 9, "pva": 10}
TOPICS = ["sim_schedule_applied", "vehicle_attitude_setpoint", "trajectory_setpoint"]
# run.json event -> sched.txt offset (us from anchor) it should start at
EVENT_OFFSET = {
    "step_roll_r1": {"settle": 3_000_000, "up": 5_000_000, "zero1": 8_000_000,
                     "down": 11_000_000, "zero2": 14_000_000},
    "traj_lemniscate_r1": {"settle": 3_000_000, "traj": 6_000_000},
}


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(lines)


def write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def parse_sched(path):
    rows, anchored = [], False
    for line in open(path):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        p = s.split()
        t, kind = int(p[0]), p[1]
        off = t if (anchored and kind != "anchor") else None
        rows.append({"t": t, "kind": kind, "f": p[2:], "offset": off})
        if kind == "anchor":
            anchored = True
    return rows


def load(path):
    tp = {}
    for d in ULog(path, message_name_filter_list=TOPICS).data_list:
        tp.setdefault(d.name, []).append(d.data)
    return tp


def need(tp, name):
    if name not in tp:
        raise SystemExit(f"topic {name} not in log; present: {sorted(tp)}")
    return tp[name][0]


def applied(data):
    n = len(data["timestamp"])
    return [{"ts": int(data["timestamp"][i]), "t_sched": int(data["t_sched_us"][i]),
             "kind": int(data["kind"][i]), "anchor": int(data["anchor_us"][i]),
             "sp": [float(data[f"sp[{k}]"][i]) for k in range(4)]} for i in range(n)]


def anchor_of(app):
    return next(a["anchor"] for a in app if a["kind"] == 6)


def check1(name, sched, app):
    by_s, by_a = {}, {}
    for r in sched:
        by_s.setdefault(KIND_CODE.get(r["kind"]), []).append(r)
    for a in app:
        by_a.setdefault(a["kind"], []).append(a)
    codes = sorted(c for c in set(by_s) | set(by_a) if c is not None)
    counts = [[c, len(by_s.get(c, [])), len(by_a.get(c, []))] for c in codes]
    unmapped = Counter(r["kind"] for r in sched if r["kind"] not in KIND_CODE)
    rows = []
    for c in codes:
        for s, a in zip(by_s.get(c, []), by_a.get(c, [])):
            off = s["offset"]
            exp = a["anchor"] + off if off is not None else None
            err = a["ts"] - exp if exp is not None else None
            ref = a["anchor"] + off if off is not None else s["t"]
            spd = None
            hold = next(h["sp"] for h in app if h["kind"] == 5)
            if c == 9:
                f = [float(v) for v in s["f"][:3]]
                spd = max(abs(a["sp"][0] - f[0]), abs(a["sp"][1] - f[1]),
                          abs(a["sp"][2] - (hold[3] + f[2])))
            elif c == 10:
                f = [float(v) for v in s["f"][:3]]
                spd = max(abs(a["sp"][k] - (hold[k] + f[k])) for k in range(3))
            rows.append({"flight": name, "kind_code": c, "sched_kind": s["kind"],
                         "sched_t_us": s["t"], "offset_us": off,
                         "applied_ts_us": a["ts"], "applied_t_sched_us": a["t_sched"],
                         "anchor_us": a["anchor"], "expected_ts_us": exp,
                         "err_us": err, "t_sched_match": a["t_sched"] == ref,
                         "sp_vs_sched_max_abs": spd})
    write_csv(os.path.join(OUT, f"check1_{name}.csv"), rows)

    errs = [r["err_us"] for r in rows if r["err_us"] is not None]
    above = [r for r in rows if r["err_us"] is not None and abs(r["err_us"]) > TOL_US]
    dup = [k for k, v in Counter((a["kind"], a["t_sched"]) for a in app).items() if v > 1]
    spds = [r["sp_vs_sched_max_abs"] for r in rows if r["sp_vs_sched_max_abs"] is not None]
    anc_rows = [a for a in app if a["kind"] == 6]
    print(f"\n### Check 1 {name}")
    print(md_table(["kind code", "sched rows", "applied rows"], counts))
    print(f"sched kinds without topic code (not in topic by construction): {dict(unmapped)}")
    print(f"offset rows checked: {len(errs)}; max |err| us: "
          f"{max((abs(e) for e in errs), default=0)}; mean err us: {np.mean(errs):.1f}; "
          f"rows > {TOL_US} us: {len(above)}")
    print(f"applied rows with t_sched mismatch: {sum(not r['t_sched_match'] for r in rows)}; "
          f"duplicate (kind, t_sched) in topic: {len(dup)}; "
          f"max |sp - sched value| (roll/pitch/yaw or x/y/z): {max(spds, default=0):.2e}")
    print(f"anchor row: applied timestamp {anc_rows[0]['ts']} vs anchor_us {anc_rows[0]['anchor']} "
          f"(diff {anc_rows[0]['ts'] - anc_rows[0]['anchor']} us)")
    print(f"  sp_hold (kind 5) sp = {[round(v, 4) for v in next(h['sp'] for h in app if h['kind'] == 5)]}")
    seen = set()
    for r in rows:
        if r["kind_code"] in (1, 3, 5, 9, 10, 11) and r["kind_code"] not in seen:
            seen.add(r["kind_code"])
            print(f"  first kind {r['kind_code']}: sched t {r['sched_t_us']} offset {r['offset_us']} "
                  f"applied t_sched {r['applied_t_sched_us']} ts {r['applied_ts_us']}")
    for r in rows:
        if r["kind_code"] in (1, 3, 5, 11):
            print(f"  kind {r['kind_code']}: sched t {r['sched_t_us']} applied t_sched "
                  f"{r['applied_t_sched_us']} ts {r['applied_ts_us']} anchor {r['anchor_us']}")
    for r in above[:10]:
        print(f"  above tol: kind {r['kind_code']} offset {r['offset_us']} err {r['err_us']} us")
    return rows


def check2(sched, app, att):
    anchor = anchor_of(app)
    ts = np.asarray(att["timestamp"]).astype(np.int64)
    q = [np.asarray(att[f"q_d[{k}]"], float) for k in range(4)]
    roll = np.degrees(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]), 1 - 2 * (q[1] ** 2 + q[2] ** 2)))
    jumps = np.nonzero(np.abs(np.diff(roll)) > 0.5)[0] + 1
    chg = []
    for k, j in enumerate(jumps):
        end = jumps[k + 1] if k + 1 < len(jumps) else len(roll)
        chg.append([f"{(ts[j] - anchor) / 1e6:.3f}", f"{roll[j - 1]:.2f}", f"{roll[j]:.2f}",
                    f"{np.median(roll[j:end]):.2f}"])
    rows = []
    for r in sched:
        if r["kind"] != "att":
            continue
        e = anchor + r["offset"]
        target = float(np.degrees(float(r["f"][0])))
        w = (ts >= e + 300000) & (ts <= e + 700000)
        plat = float(np.median(roll[w])) if w.any() else float("nan")
        hit = np.nonzero((ts >= e - 100000) & (np.abs(roll - target) < 0.5))[0]
        lat = f"{(ts[hit[0]] - e) / 1e3:.1f}" if len(hit) else "none"
        rows.append([f"{r['offset'] / 1e6:.3f}", f"{target:.2f}", lat, f"{plat:.2f}",
                     f"{plat - target:+.2f}"])
    print("\n### Check 2 step_roll_r1: vehicle_attitude_setpoint roll (from q_d)")
    print(md_table(["sched offset s", "sched roll deg", "first reach latency ms (+/-0.5 deg)",
                    "log roll median +0.3..+0.7 s", "diff deg"], rows))
    print("\nlog roll jumps > 0.5 deg between samples:")
    print(md_table(["t rel anchor s", "roll before", "roll after", "plateau median"], chg))
    return rows, chg


def check3(name, sched, app, tsp):
    ps = [r for r in sched if r["kind"] == "pva"]
    pa = [a for a in app if a["kind"] == 10]
    hold_rows = [a for a in app if a["kind"] == 5]
    hold = np.array(hold_rows[0]["sp"][:3]) if hold_rows else np.full(3, np.nan)
    n = min(len(ps), len(pa))
    print(f"\n### Check 3 {name}: pva rows sched {len(ps)} applied {len(pa)}; "
          f"hold (sp_hold kind 5) x y z = {np.round(hold, 4).tolist()}")
    tts = np.asarray(tsp["timestamp"]).astype(np.int64)
    P = np.stack([np.asarray(tsp[f"position[{k}]"], float) for k in range(3)], axis=1)
    raw = np.array([[float(v) for v in r["f"][:3]] for r in ps[:n]])
    ats = np.array([a["ts"] for a in pa[:n]], dtype=np.int64)
    J = np.searchsorted(tts, ats, side="left")
    Jc = np.minimum(J, len(tts) - 1)
    dt_ms = (tts[Jc] - ats) / 1e3
    Pm = P[Jc]
    err_raw = np.linalg.norm(Pm - raw, axis=1)
    err_hold = np.linalg.norm(Pm - (hold + raw), axis=1)
    f3 = lambda v: [f"{x:.3f}" for x in v]
    idx = np.round(np.linspace(0, n - 1, 5)).astype(int)
    rows = []
    for i in idx:
        rows.append([int(i), f"{ps[i]['offset'] / 1e6:.3f}", " ".join(f3(raw[i])),
                     f"{ats[i] / 1e6:.3f}", f"{dt_ms[i]:.1f}", " ".join(f3(Pm[i])),
                     f"{err_raw[i]:.3f}", f"{err_hold[i]:.3f}"])
    print(md_table(["pva idx", "sched offset s", "sched x y z", "applied ts s",
                    "TSP ts - applied ms", "TSP x y z", "err raw (m)", "err hold+sched (m)"], rows))
    print(f"all {n} rows: median err raw {np.median(err_raw):.3f} m, "
          f"median err hold+sched {np.median(err_hold):.3f} m, max err hold+sched "
          f"{np.max(err_hold):.3f} m; TSP sample gap after applied ts: min {np.min(dt_ms):.1f} "
          f"max {np.max(dt_ms):.1f} ms; rows with no later TSP sample: {int(np.sum(J >= len(tts)))}")
    write_csv(os.path.join(OUT, f"check3_{name}.csv"),
              [{"idx": int(i), "offset_us": ps[i]["offset"], "sched_x": raw[i][0],
                "sched_y": raw[i][1], "sched_z": raw[i][2], "applied_ts_us": int(ats[i]),
                "tsp_ts_us": int(tts[Jc[i]]), "tsp_x": Pm[i][0], "tsp_y": Pm[i][1],
                "tsp_z": Pm[i][2], "err_raw_m": err_raw[i], "err_hold_m": err_hold[i]}
               for i in range(n)])
    return rows


def check4(name, rj, app, sched):
    anchor = anchor_of(app)
    anc_ts = next(a["ts"] for a in app if a["kind"] == 6)
    last_pva = max(r["offset"] for r in sched if r["kind"] == "pva") if name.startswith("traj") else None
    rows = []
    for ev in rj["events"]:
        off = EVENT_OFFSET[name].get(ev["name"])
        if ev["name"] == "hold" and last_pva is not None:
            off = last_pva
        implied = ev["t_us"] - off if off is not None else None
        rows.append([ev["name"], ev["t_us"], off, implied,
                     f"{(implied - anchor) / 1e3:+.3f}" if implied is not None else "n/a"])
    for key in ("sched_t0_us", "t_window_start_us", "t_window_end_us"):
        if key in rj:
            rows.append([key, rj[key], "", "", f"{(rj[key] - anchor) / 1e3:+.3f} (vs anchor)"])
    print(f"\n### Check 4 {name}: log anchor_us {anchor} (anchor row ts {anc_ts}); "
          f"run.json t_offboard_us {rj.get('t_offboard_us')} "
          f"(vs anchor {(rj.get('t_offboard_us', 0) - anchor) / 1e3:+.3f} ms)")
    print(md_table(["run.json item", "t_us", "sched offset us", "implied anchor us",
                    "implied - log anchor (ms)"], rows))


def main():
    os.makedirs(OUT, exist_ok=True)
    for name in ["step_roll_r1", "traj_lemniscate_r1"]:
        d = os.path.join(RES, name)
        sched = parse_sched(os.path.join(d, "sched.txt"))
        tp = load(os.path.join(d, "flight.ulg"))
        app = applied(need(tp, "sim_schedule_applied"))
        with open(os.path.join(d, "run.json")) as fh:
            rj = json.load(fh)
        print(f"\n==== {name}: {len(sched)} sched rows, {len(app)} applied rows")
        check1(name, sched, app)
        if name == "step_roll_r1":
            check2(sched, app, need(tp, "vehicle_attitude_setpoint"))
        else:
            check3(name, sched, app, need(tp, "trajectory_setpoint"))
        check4(name, rj, app, sched)


if __name__ == "__main__":
    main()
