#!/usr/bin/env python3
"""A-24 check: residual ~46 Hz tone in actuator_motors control[0..3] and angular velocity, hover logs."""
import os
import numpy as np
from pyulog import ULog

ROOT = "/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results"
LOGS = [
    ("REF s45 indi_g1y (G2_Y?)", f"{ROOT}/stage2_s45/a23_yaw/indi_g1y/flight.ulg", "reference"),
    ("measured_g2 seed1", f"{ROOT}/stage2_s47/roll_m3a/measured_g2/flight.ulg", "plain hover, G2_Y 27"),
    ("measured_g2_s2 seed2", f"{ROOT}/stage2_s47/roll_m3a/measured_g2_s2/flight.ulg", "plain hover, G2_Y 27"),
    ("model_g2 seed1", f"{ROOT}/stage2_s47/roll_m3a/model_g2/flight.ulg", "plain hover, G2_Y 27"),
    ("model_g2_s2 seed2", f"{ROOT}/stage2_s47/roll_m3a/model_g2_s2/flight.ulg", "plain hover, G2_Y 27"),
    ("model_g2_a001 seed1", f"{ROOT}/stage2_s47/roll_m3a/model_g2_a001/flight.ulg", "SINE a001 injection, report separately"),
]
TOPICS = ["vehicle_land_detected", "actuator_motors", "vehicle_angular_velocity"]


def get(ulog, name):
    for d in ulog.data_list:
        if d.name == name and d.multi_id == 0:
            return d.data
    return None


def welch(x, fs, nper):
    step = nper // 2
    w = np.hanning(nper)
    starts = range(0, len(x) - nper + 1, step)
    S = np.zeros(nper // 2 + 1)
    for s in starts:
        S += np.abs(np.fft.rfft(x[s:s + nper] * w)) ** 2
    S /= len(starts)
    S /= fs * np.sum(w ** 2)
    S[1:-1] *= 2.0
    return np.fft.rfftfreq(nper, 1.0 / fs), S


def spectrum(x, fs):
    tt = np.arange(len(x)) / fs
    xd = x - np.polyval(np.polyfit(tt, x, 1), tt)
    nper = min(len(xd), int(round(2.0 * fs)))
    f, P = welch(xd, fs, nper)
    df = f[1] - f[0]
    top = min(100.0, 0.5 * fs)
    band = (f >= 20) & (f <= top)
    i = int(np.argmax(np.where(band, P, -np.inf)))
    med = float(np.median(P[band]))
    if 0.5 * fs > 50:
        b = (f >= 40) & (f <= 50)
        bstd = float(np.sqrt(np.sum(P[b]) * df))  # PSD integration over 40-50 Hz
    else:
        bstd = float("nan")
    return dict(std=float(np.std(xd)), peak_hz=float(f[i]), peak_p=float(P[i]),
                ratio=float(P[i] / med), band_std=bstd, top=top)


def analyse_log(path):
    u = ULog(path, message_name_filter_list=TOPICS)
    params = u.initial_parameters
    ld = get(u, "vehicle_land_detected")
    am = get(u, "actuator_motors")
    av = get(u, "vehicle_angular_velocity")
    t_ld = ld["timestamp"] * 1e-6
    landed = ld["landed"].astype(int)
    if not np.any(landed == 0):
        raise RuntimeError("landed never false")
    t_air = t_ld[np.argmax(landed == 0)]
    after = np.where((t_ld > t_air) & (landed == 1))[0]
    t_land = t_ld[after[0]] if len(after) else np.inf
    t_end_log = max(am["timestamp"][-1], av["timestamp"][-1]) * 1e-6
    t0 = t_air + 15.0
    t1 = min(t_end_log - 15.0, t_land)
    out = dict(params={k: params.get(k) for k in ["MC_INDI_G1_Y", "MC_INDI_G2_Y"]},
               t_air=float(t_air), t0=float(t0), t1=float(t1), t_land=float(t_land),
               window_s=float(t1 - t0), rows=[])
    am_dt = float(np.median(np.diff(am["timestamp"]))) * 1e-6
    av_dt = float(np.median(np.diff(av["timestamp"]))) * 1e-6
    out["am_rate"] = 1.0 / am_dt
    out["av_rate"] = 1.0 / av_dt
    t = am["timestamp"] * 1e-6
    m = (t >= t0) & (t < t1)
    tg = t[m]
    fs = 1.0 / am_dt
    tt = np.arange(tg[0], tg[-1], 1.0 / fs)
    for i in range(4):
        x = am[f"control[{i}]"][m].astype(float)
        xr = np.interp(tt, tg, x)
        s = spectrum(xr, fs)
        s.update(log_mean=float(np.mean(x)), name=f"motor{i}")
        out["rows"].append(s)
    ta = av["timestamp"] * 1e-6
    ma = (ta >= t0) & (ta < t1)
    tga = ta[ma]
    fsa = 1.0 / av_dt
    tta = np.arange(tga[0], tga[-1], 1.0 / fsa)
    for ax, lab in enumerate("xyz"):
        x = av[f"xyz[{ax}]"][ma].astype(float)
        xr = np.interp(tta, tga, x)
        s = spectrum(xr, fsa)
        s.update(log_mean=float(np.mean(x)), name=f"angvel {lab}")
        out["rows"].append(s)
    return out


if __name__ == "__main__":
    for name, path, kind in LOGS:
        print(f"\n### {name} [{kind}]  {path}")
        if not os.path.exists(path):
            print("MISSING")
            continue
        try:
            r = analyse_log(path)
        except Exception as e:  # report and continue
            print(f"ERROR {e}")
            continue
        print(f"params G1_Y={r['params']['MC_INDI_G1_Y']} G2_Y={r['params']['MC_INDI_G2_Y']}")
        print(f"landed false at {r['t_air']:.2f}s, land true at {r['t_land']:.2f}s, window [{r['t0']:.2f},{r['t1']:.2f}) len {r['window_s']:.1f}s")
        print(f"logged rate actuator_motors {r['am_rate']:.1f} Hz (half {r['am_rate']/2:.1f}); angvel {r['av_rate']:.1f} Hz")
        for s in r["rows"]:
            print(f"{s['name']}|mean {s['log_mean']:.5f}|std {s['std']:.4e}|peak {s['peak_hz']:.2f} Hz|P {s['peak_p']:.3e}|peak/med {s['ratio']:.2f}|band40-50 std {s['band_std']:.4e}|top {s['top']:.1f}")
