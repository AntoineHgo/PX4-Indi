#!/usr/bin/env python3
"""Key 2, G4 command chatter with the Q18 A land-window skip (GATES.md, Owner amendments S180).

Same detector as g3_checks_key2.chatter (Q14 A: 4 s windows, 20-100 Hz, peak > 20 x band median AND line RMS +-2 Hz >= 5e-4,
>= 3 consecutive windows within +-10 % frequency), plus: windows overlapping [ground_contact - 1 s, landed + 1 s] are skipped.
ground_contact = last rise of vehicle_land_detected.ground_contact (0 -> 1); landed = the next rise of .landed after it.
No ground_contact rise or no landed rise afterwards -> nothing skipped (reported as such).
Usage: g4_chatter_skip_key2.py [--self-test [--break]] run_dir...
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import g3_checks_key2 as K

MARGIN_S = 1.0
BREAK = False   # --break disables the skip, to prove the self-test bites

def land_window(ld_t, gc, landed):
    """-> (t_gc, t_landed) of the final descent or None. Arrays: land-detected timestamps (s), ground_contact, landed."""
    gc = np.asarray(gc) > 0; landed = np.asarray(landed) > 0; ld_t = np.asarray(ld_t)
    rises = [i for i in range(1, len(gc)) if gc[i] and not gc[i - 1]]
    if not rises: return None
    i = rises[-1]
    lr = [j for j in range(max(i, 1), len(landed)) if landed[j] and not landed[j - 1]]
    if not lr: return None
    return float(ld_t[i]), float(ld_t[lr[0]])

def chatter(t, u, win=None):
    """t (s), u (n,4) commands over the airborne span; win = (t_gc, t_landed) or None. Returns per-motor dict."""
    tg, g = K.grid(t, u); res = {}
    skip = [] if (win is None or BREAK) else [(win[0] - MARGIN_S, win[1] + MARGIN_S)]
    for i in range(4):
        sk = []; wins = K.psd_windows(g[:, i], K.FS, 20, 100, rms_hz=2.0, t_off=tg[0], skip=skip, skipped=sk)
        s = K.sustained(wins, rms_min=K.DSHOT_STEP)
        ta = [tg[0] + x[0] for x in wins]
        live = [(x, a) for x, a in zip(wins, ta) if a not in sk]
        fl = [(x, a) for x, a in live if x[2] > K.RATIO and x[3] >= K.DSHOT_STEP]
        wb = max(fl, key=lambda p: p[0][3]) if fl else max(live, key=lambda p: p[0][2])
        # worst skipped-window line: recompute without skip for the skipped windows only
        sk_worst = None
        if sk:
            allw = K.psd_windows(g[:, i], K.FS, 20, 100, rms_hz=2.0, t_off=tg[0])
            cand = [(x, tg[0] + x[0]) for x in allw if (tg[0] + x[0]) in sk]
            b = max(cand, key=lambda p: p[0][3]); sk_worst = {"f_hz": b[0][1], "ratio": b[0][2], "rms": b[0][3], "t_start": b[1]}
        res[f"m{i}"] = {"sustained": s is not None, "at": s, "n_flagged": len(fl), "n_skipped": len(sk),
                        "worst": {"f_hz": wb[0][1], "ratio": wb[0][2], "rms": wb[0][3], "t_start": wb[1]},
                        "skipped_worst": sk_worst}
    return res

def load(d):
    from pyulog import ULog
    u = ULog(os.path.join(d, "flight.ulg"), message_name_filter_list=["sim_ground_truth", "actuator_motors", "vehicle_land_detected"])
    D = {x.name: x.data for x in u.data_list}; g = D["sim_ground_truth"]; t = g["timestamp"] * 1e-6
    pos = np.stack([g["x"], g["y"], g["z"]], 1); z0 = np.median(pos[:800, 2])
    ev = [e for e in json.load(open(os.path.join(d, "run.json")))["events"] if e["name"] == "hold"][0]
    h0, h1 = ev["t_us"] * 1e-6, ev["t_us"] * 1e-6 + ev["dur_s"]
    sgn = 1.0 if np.median(pos[(t > h0) & (t < h1), 2]) > z0 else -1.0
    h = sgn * (pos[:, 2] - z0)
    air = h > h[:800].mean() + 0.3; ia = np.where(air)[0]; a0, a1 = t[ia[0]], t[ia[-1]]   # same airborne span as key 2
    mo = D["actuator_motors"]; mt = mo["timestamp"] * 1e-6; mm = (mt >= a0) & (mt <= a1)
    u4 = np.stack([mo[f"control[{i}]"] for i in range(4)], 1)
    ld = D["vehicle_land_detected"]
    return mt[mm], u4[mm], land_window(ld["timestamp"] * 1e-6, ld["ground_contact"], ld["landed"]), (a0, a1)

def score(d):
    mt, u, win, span = load(d); ch = chatter(mt, u, win)
    fl = [k for k, v in ch.items() if v["sustained"]]
    w = max(ch.values(), key=lambda v: v["worst"]["rms"] if v["n_flagged"] else -v["worst"]["ratio"])
    sks = [v["skipped_worst"] for v in ch.values() if v["skipped_worst"]]
    return {"chatter": fl, "win": win, "span": span, "worst": w["worst"], "motor": [k for k, v in ch.items() if v is w][0],
            "skipped_worst": max(sks, key=lambda x: x["rms"]) if sks else None, "motors": ch}

# ---- synthetic self-test --------------------------------------------------------------------------------------------
def _synth(line_hz, t_on, t_off, amp=0.03, T=60.0, seed=0):
    t = np.arange(0, T, 1 / K.FS); rng = np.random.default_rng(seed)
    u = 0.14 + rng.normal(0, 0.003, (len(t), 4)); on = (t >= t_on) & (t < t_off)
    u[on, 1] += amp * np.sin(2 * np.pi * line_hz * t[on]); return t, u

def self_test():
    ok = True
    def chk(name, got, want):
        nonlocal ok; good = got == want; ok &= good; print(("PASS " if good else "FAIL ") + name, "got", got, "want", want)
    # land_window on a synthetic topic log (two rises of gc: takeoff-style first sample 1 is not a rise; last rise used)
    chk("land_window", land_window([0, 5, 6, 50, 52, 53], [1, 0, 0, 1, 1, 1], [1, 0, 0, 0, 1, 1]), (50.0, 52.0))
    chk("land_window no landing", land_window([0, 5, 50], [1, 0, 1], [1, 0, 0]), None)
    chk("land_window no ground_contact rise", land_window([0, 5], [1, 0], [1, 0]), None)
    win = (40.0, 42.0)   # skip interval = [39, 43]; 4 s windows start every 1 s
    def run(t_on, t_off, w=win):
        t, u = _synth(70, t_on, t_off); return chatter(t, u, w)["m1"]["sustained"]
    chk("70 Hz line only inside land window, skipped -> not flagged", run(39.0, 43.0), False)
    chk("70 Hz line far outside window -> flagged", run(5.0, 25.0), True)
    chk("same early line, no landing at all -> flagged", run(5.0, 25.0, None), True)
    # window edge: line 33..36 s then silence; 4 s windows starting 33,34,35 (all end <= 39 = skip start) are NOT skipped.
    # windows start 36..: start 36 ends 40 > 39 overlaps -> skipped. Line 30..38 -> windows 30..34 clean (>=3) -> flagged
    chk("line ends right before skip edge (windows ending <= 39) -> flagged", run(30.0, 39.0), True)
    # line only in [39,43): windows starting 35 (ends 39) sees none; windows start 36..42 overlap skip -> all skipped
    chk("line [39,43) all overlapping windows skipped -> not flagged", run(39.0, 43.0), False)
    # line after the skip edge: from 43 to 60; windows start >= 43 are not skipped (start 43 == skip end, no overlap)
    chk("line from 43 s on (window start 43 touches edge, not overlapping) -> flagged", run(43.0, 60.0), True)
    # line from 42.5: windows starting 43.. contain 3.5 s of line, not skipped (>=3) -> flagged
    chk("line from 42.5 s on -> flagged", run(42.5, 60.0), True)
    # skipped worst reporting
    t, u = _synth(70, 39.0, 43.0); r = chatter(t, u, win)["m1"]
    chk("skipped worst line ~70 Hz reported", (r["skipped_worst"] is not None and abs(r["skipped_worst"]["f_hz"] - 70) < 1), True)
    chk("skipped window count (starts 36..42 -> 7)", r["n_skipped"], 7)
    return ok

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--break" in a: BREAK = True
    if "--self-test" in a: sys.exit(0 if self_test() else 1)
    for d in (x for x in a if not x.startswith("--")):
        r = score(d); n = os.path.basename(d.rstrip("/")); w = r["worst"]; s = r["skipped_worst"]
        print(json.dumps({"run": n, "chatter": r["chatter"], "gc_landed": r["win"], "span": r["span"], "worst_motor": r["motor"],
                          "worst": w, "skipped_worst": s}, default=float))
