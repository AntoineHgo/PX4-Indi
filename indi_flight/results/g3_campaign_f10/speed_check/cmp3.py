#!/usr/bin/env python3
"""Three-way G3 draw comparison: s1a (pre-test, speed 1), s1b (repeat, speed 1), s4 (speed 4)."""
import json, os, statistics as st

R = "/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results"
S4, S1B = f"{R}/g3_speed4_check_f10", f"{R}/g3_speed1_repeat_f10"


def s1a(i):
    d = f"{R}/g3_pretest_q24_s197"
    return d if os.path.isdir(f"{d}/run_{i:03d}") else f"{R}/freeze10_s193/g3_pretest"


def load(p):
    try:
        return json.load(open(p))
    except Exception:
        return None


def mets(c):
    m = {}
    if not c:
        return m
    i1, i3 = c.get("item1_loc", {}), c.get("item3_steady_state", {})
    m["tilt_max_deg"] = (i1.get("tilt_max_deg"), 60.0)
    for k in ("horizontal_rms_m", "altitude_mean_m"):
        e = i3.get(k) or {}
        m[k] = (e.get("value"), e.get("threshold"))
    rp = i3.get("roll_pitch_mean_deg") or {}
    if isinstance(rp.get("value"), list):
        m["roll_mean_deg"] = (rp["value"][0], rp.get("threshold"))
        m["pitch_mean_deg"] = (rp["value"][1], rp.get("threshold"))
    return m


def osc(c):
    return "".join(a for a in "pqr" if c and c["item2_oscillation"][a]["sustained"])


def k2(root, i):
    j = load(f"{root}/key2/run_{i:03d}.json")
    return None if j is None else j.get("pass")


keys = ["tilt_max_deg", "horizontal_rms_m", "altitude_mean_m", "roll_mean_deg", "pitch_mean_deg"]
rep, spd_a, spd_b = {k: [] for k in keys}, {k: [] for k in keys}, {k: [] for k in keys}
flips = {"s1a-s1b k1": [], "s1a-s1b k2": [], "s4-s1a k1": [], "s4-s1a k2": [], "s4-s1b k1": [], "s4-s1b k2": []}
print("idx  k1 a/b/4   k2 a/b/4   osc a/b/4   altitude_mean a / b / 4 (thr)")
for i in range(20):
    a_root = s1a(i)
    ca, cb, c4 = (load(f"{r}/run_{i:03d}/g3_checks.json") for r in (a_root, S1B, S4))
    if cb is None:
        print(f"{i:02d} repeat missing")
        continue
    k1 = [c.get("pass") if c else None for c in (ca, cb, c4)]
    kk2 = [k2(a_root, i), k2(S1B, i), k2(S4, i)]
    for (x, y, nm) in ((0, 1, "s1a-s1b"), (0, 2, "s4-s1a"), (1, 2, "s4-s1b")):
        if k1[x] != k1[y]:
            flips[nm + " k1"].append(i)
        if kk2[x] != kk2[y]:
            flips[nm + " k2"].append(i)
    ma, mb, m4 = mets(ca), mets(cb), mets(c4)
    for k in keys:
        try:
            (va, th), (vb, _), (v4, _) = ma[k], mb[k], m4[k]
            th = th or 1.0
            rep[k].append(abs(vb - va) / th)
            spd_a[k].append(abs(v4 - va) / th)
            spd_b[k].append(abs(v4 - vb) / th)
        except Exception:
            pass
    alt = [m.get("altitude_mean_m", (None, None)) for m in (ma, mb, m4)]
    print(f"{i:02d}  {k1}  {kk2}  {[osc(c) for c in (ca, cb, c4)]}  "
          + " / ".join(f"{v[0]:+.3f}" if isinstance(v[0], float) else "?" for v in alt) + f" ({alt[0][1]})")

print("\nverdict flips:", {k: v for k, v in flips.items()})
print("\n|diff| as fraction of threshold: median / max    repeat(s1a-s1b) | s4-s1a | s4-s1b")
for k in keys:
    f = lambda L: f"{st.median(L):.2f}/{max(L):.2f}" if L else "-"
    print(f"  {k:18s} {f(rep[k]):>12s} | {f(spd_a[k]):>12s} | {f(spd_b[k]):>12s}")
