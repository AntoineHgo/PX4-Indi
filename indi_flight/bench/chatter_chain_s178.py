#!/usr/bin/env python3
"""S178 chatter chain: line (L1 ~33 Hz offboard lemniscate, L2 ~21 Hz AUTO_LAND) strength per signal along the control chain.
usage: chatter_chain_s178.py [--out md] log.ulg [label ...]   (host python3: pyulog + numpy only)
Per signal component: Welch (2 s Hann, 50 %), peak PSD in the line band over median PSD of 20..0.9*Nyquist (peak/floor),
line RMS (+-1 Hz) in native units. Components above 0.9*Nyquist of the topic's logged rate are reported 'n/a'.
Output is bounded: best component per signal, plus motor collective / differential modes."""
import sys
import numpy as np

# name: (t0, t1, line band Hz, Welch segment s). L2d = AUTO_LAND constant-rate descent (~0.7 m/s, z -4 -> -0.5 m), L2g = on ground
# after land-detector (landed 68-69 s, disarm 70-71 s); the old 65-72 window mixes descent and touchdown.
WINDOWS = {"ctl(18-28)": (18, 28, (30, 37), 2.0), "L1(38-52)": (38, 52, (30, 37), 2.0),
           "L2d(62-66.5)": (62, 66.5, (18, 25), 1.5), "L2g(69.5-72)": (69.5, 72, (18, 25), 1.0)}


def uniform(t, x, fs):
    tg = np.arange(t[0], t[-1], 1.0 / fs)
    return tg, np.interp(tg, t, x)


def line_stat(t, x, w0, w1, band, fs_nom=None, seg_s=2.0):
    """returns (peak_hz, ratio, line_rms) or None if not resolvable"""
    dt = np.median(np.diff(t))
    fs = fs_nom or 1.0 / dt
    nyq = fs / 2
    if band[0] >= 0.9 * nyq or w1 - w0 < 1.5 * seg_s:
        return None
    tg, g = uniform(t, x, fs)
    m = (tg >= w0) & (tg < w1)
    g = g[m]
    n = int(seg_s * fs)
    if len(g) < n + n // 2:
        return None
    w = np.hanning(n)
    P = 0
    cnt = 0
    for s in range(0, len(g) - n + 1, n // 2):
        seg = g[s:s + n]
        seg = (seg - seg.mean()) * w
        P = P + np.abs(np.fft.rfft(seg)) ** 2
        cnt += 1
    P = P / cnt / (fs * (w ** 2).sum())
    f = np.fft.rfftfreq(n, 1.0 / fs)
    df = f[1] - f[0]
    fb = (f >= 20) & (f <= min(100, 0.9 * nyq))
    floor = np.median(P[fb])
    bm = (f >= band[0]) & (f <= min(band[1], 0.9 * nyq))
    k = np.flatnonzero(bm)[np.argmax(P[bm])]
    rms = float(np.sqrt(P[(f >= f[k] - 1) & (f <= f[k] + 1)].sum() * df))
    return float(f[k]), float(P[k] / max(floor, 1e-30)), rms


def comp_names(d, prefix_fields):
    out = []
    for k in d.data:
        if k.startswith("_") or k in ("timestamp", "timestamp_sample"):
            continue
        if any(k == p or k.startswith(p + "[") for p in prefix_fields):
            out.append(k)
    return out


# (label, topic, instance, fields)
SPEC = [
    ("pos_sp/lpos_sp x,y,z,v", "vehicle_local_position_setpoint", 0, ["x", "y", "z", "vx", "vy", "vz", "acceleration", "thrust"]),
    ("lpos (estimate)", "vehicle_local_position", 0, ["vx", "vy", "vz", "ax", "ay", "az"]),
    ("outer a_c (indi_pos)", "indi_pos_status", 0, ["a_c", "a_c_pre_inject", "inject"]),
    ("outer a_f (filt spec.force)", "indi_pos_status", 0, ["a_f", "t_f"]),
    ("outer t_c/t_c_applied", "indi_pos_status", 0, ["t_c", "t_c_applied", "omega_ff", "mean_u", "thrust"]),
    ("att_sp q_d,thrust_body", "vehicle_attitude_setpoint", 0, ["q_d", "thrust_body"]),
    ("rates_sp (267Hz)", "vehicle_rates_setpoint", 0, ["roll", "pitch", "yaw", "thrust_body"]),
    ("vehicle_acceleration", "vehicle_acceleration", 0, ["xyz"]),
    ("gyro (angular_velocity)", "vehicle_angular_velocity", 0, ["xyz"]),
    ("inner nu/alpha_f/tau_f", "indi_rate_status", 0, ["nu", "angular_accel_filtered", "torque_filtered"]),
    ("inner dtau/rates_sp_applied", "indi_rate_status", 0, ["torque_increment", "rates_sp_applied", "torque_sp"]),
    ("torque_setpoint", "vehicle_torque_setpoint", 0, ["xyz"]),
    ("thrust_setpoint", "vehicle_thrust_setpoint", 0, ["xyz"]),
    ("torque_measured", "actuator_torque_measured", 0, ["torque"]),
]


def motor_modes(M):
    """M: (n,4) -> dict mode->series; Hadamard modes (geometry independent)"""
    a, b, c, d = M.T
    return {"collective": (a + b + c + d) / 4, "diffA": (a + b - c - d) / 4, "diffB": (a - b + c - d) / 4, "diffC": (a - b - c + d) / 4}


def analyse(log, label=""):
    from pyulog import ULog
    u = ULog(log)
    t0 = u.start_timestamp
    rows = []
    rates = {}

    def tt(d):
        return (d.data["timestamp"].astype(np.int64) - t0) * 1e-6

    def rec(name, t, x, key=None):
        r = {}
        for wn, (w0, w1, band, sg) in WINDOWS.items():
            r[wn] = line_stat(t, x, w0, w1, band, seg_s=sg)
        rows.append((name, key or "", r))

    for lab, topic, inst, flds in SPEC:
        try:
            d = u.get_dataset(topic, inst)
        except Exception:
            continue
        t = tt(d)
        rates[lab] = (len(t) - 1) / (t[-1] - t[0])
        best = None
        for k in comp_names(d, flds):
            x = d.data[k].astype(float)
            if not np.isfinite(x).all() or np.ptp(x) == 0:
                continue
            r = {wn: line_stat(t, x, w0, w1, band, seg_s=sg) for wn, (w0, w1, band, sg) in WINDOWS.items()}
            sc = max((v[1] for v in r.values() if v), default=-1)
            if best is None or sc > best[0]:
                best = (sc, k, r)
        if best:
            rows.append((lab, best[1], best[2]))
        else:
            rows.append((lab, "n/a (nyq %.0f Hz)" % (rates[lab] / 2), {w: None for w in WINDOWS}))
    d = u.get_dataset("actuator_motors")
    t = tt(d)
    M = np.stack([d.data["control[%d]" % i] for i in range(4)], 1)
    for k, x in motor_modes(M).items():
        rec("actuator_motors " + k, t, x)
    rates["actuator_motors"] = (len(t) - 1) / (t[-1] - t[0])
    try:
        d = u.get_dataset("esc_status", 0)
        t = tt(d)
        R = np.stack([d.data["esc[%d].esc_rpm" % i].astype(float) for i in range(4)], 1)
        if np.ptp(R) > 0:
            for k, x in motor_modes(R).items():
                rec("esc rpm " + k, t, x)
    except Exception:
        pass
    return rows, rates


def fmt(rows, rates, label):
    L = ["#### " + label, "logged Hz: " + ", ".join("%s %.0f" % (k, v) for k, v in rates.items()),
         "| signal | comp | " + " | ".join(WINDOWS) + " |", "|---|---|" + "---|" * len(WINDOWS)]
    for n, k, r in rows:
        cells = []
        for w in WINDOWS:
            v = r[w]
            cells.append("n/a" if v is None else "%.1fHz x%.1f rms%.1e" % v)
        L.append("| %s | %s | %s |" % (n, k, " | ".join(cells)))
    return "\n".join(L)


if __name__ == "__main__":
    a = sys.argv[1:]
    out = None
    if a[:1] == ["--out"]:
        out, a = a[1], a[2:]
    txt = "\n\n".join(fmt(*analyse(p), p) for p in a)
    print(txt)
    if out:
        open(out, "w").write(txt + "\n")
