#!/usr/bin/env python3
"""20 Hz line localisation along the chain. Usage: line20.py <run dir> [pair ...] | line20.py --selftest
Per signal: line RMS in 19.5-21.0 Hz (Hann PSD, 4 s windows) at windows overlapping [c,c+3 s] (max), at steady windows
c+10..c+16 (max), and the floor (rms of 15-18.5 Hz + 22.5-26 Hz bands, same width scaled). Also time course (2 s windows, hop 1 s)."""
import sys, os, json, numpy as np
from pyulog import ULog
FS = 800.0
SIG = {"actuator_motors": [f"control[{i}]" for i in range(4)], "vehicle_torque_setpoint": ["xyz[0]", "xyz[1]", "xyz[2]"],
       "vehicle_thrust_setpoint": ["xyz[2]"], "vehicle_rates_setpoint": ["roll", "pitch", "yaw", "thrust_body[2]"],
       "vehicle_attitude_setpoint": ["q_d[0]", "q_d[1]", "q_d[2]", "q_d[3]", "thrust_body[2]"],
       "indi_pos_status": None, "vehicle_angular_velocity": ["xyz[0]", "xyz[1]", "xyz[2]"],
       "esc_status": None, "indi_rate_status": None, "vehicle_acceleration": ["xyz[0]", "xyz[1]", "xyz[2]"]}
def band(x, t0, win, f0=19.5, f1=21.0):
    n = int(win * FS); s = int((t0) * FS)
    if s < 0 or s + n > len(x): return None
    w = np.hanning(n); seg = x[s:s + n] - x[s:s + n].mean(); X = np.fft.rfft(seg * w)
    P = np.abs(X) ** 2 / (FS * np.sum(w ** 2)); P[1:-1] *= 2; f = np.fft.rfftfreq(n, 1 / FS); df = f[1]
    r = lambda a, b: P[(f >= a) & (f <= b)].sum() * df
    fl = np.sqrt((r(15, 18.5) + r(22.5, 26)) / 6.5 * (f1 - f0))
    k = (f >= f0) & (f <= f1); return np.sqrt(r(f0, f1)), fl, X[k][np.argmax(np.abs(X[k]))]
def grid(t, y):
    tg = np.arange(t[0], t[-1], 1 / FS); return tg, np.interp(tg, t, y)
def load(d):
    u = ULog(os.path.join(d, "flight.ulg")); D = {}
    for x in u.data_list: D.setdefault(x.name, x.data)  # multi_id 0
    return D
def chans(D):
    out = {}
    for tp, fl in SIG.items():
        if tp not in D: continue
        dd = D[tp]; t = dd["timestamp"] * 1e-6
        names = fl or [k for k in dd if k != "timestamp" and not k.startswith(("_", "timestamp")) and dd[k].dtype.kind == "f" and np.std(dd[k]) > 0][:40]
        for k in names:
            if k in dd: out[f"{tp}.{k}"] = (t, dd[k].astype(float), len(t) / (t[-1] - t[0]))
    return out
def analyse(d, pairs=None):
    D = load(d); vs = D["vehicle_status"]; ns = vs["nav_state"]; vt = vs["timestamp"] * 1e-6
    ch = chans(D); res = []
    for j in np.flatnonzero(np.diff(ns) != 0) + 1:
        pair = f"{int(ns[j-1])}->{int(ns[j])}"
        if pairs and pair not in pairs: continue
        c = vt[j]; row = {"pair": pair, "t": float(c), "sig": {}}
        for name, (t, y, rate) in ch.items():
            tg, g = grid(t, y); tr = lambda a: a - tg[0]
            tr_ = lambda a: tr(a)
            ov = [band(g, tr(c + o), 4.0) for o in range(-3, 4)]; ov = [b for b in ov if b]
            st = [band(g, tr(c + o), 4.0) for o in range(10, 17)]; st = [b for b in st if b]
            if not ov: continue
            bi = max(ov, key=lambda b: b[0]); si = max(st, key=lambda b: b[0]) if st else None
            tc = [band(g, tr(c + o), 2.0) for o in range(-2, 8)]
            row["sig"][name] = {"rate": round(rate), "trans": bi[0], "floor": bi[1], "steady": None if si is None else si[0],
                                "ph": float(np.angle(bi[2], deg=True)), "tc": [None if b is None else b[0] for b in tc]}
        res.append(row)
    return res
def selftest():
    t = np.arange(0, 60, 1 / FS); rng = np.random.default_rng(0); x = rng.normal(0, 1e-4, len(t))
    x += 5e-4 * np.sqrt(2) * np.sin(2 * np.pi * 20.2 * t) * ((t > 20) & (t < 23))
    g = x; b = band(g, 18.0, 4.0); q = band(g, 40, 4.0)
    assert 3e-4 < b[0] < 7e-4 and q[0] < 1.5e-4 and b[0] > 3 * b[1], (b[:2], q[:2]); print("selftest ok", b[:2], q[:2])
if __name__ == "__main__":
    if sys.argv[1] == "--selftest": selftest(); sys.exit()
    print(json.dumps({"run": sys.argv[1], "res": analyse(sys.argv[1], sys.argv[2:] or None)}))
