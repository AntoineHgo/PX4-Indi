#!/usr/bin/env python3
"""Extract small decimated CSV traces from existing (untracked) flight logs for the report figures.

Reads existing .ulg files only (pyulog), never flies. Writes results/report_traces/*.csv.
Run once on a machine that still holds the logs; the figure scripts then read the committed CSVs.
"""
import os
import sys

import numpy as np
from pyulog import ULog

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))  # indi_flight/
RES = os.path.join(ROOT, "results")
OUT = os.path.join(RES, "report_traces")
FS = 200.0  # output rate, Hz

STEP_RUNS = {
    "indi": "freeze10_s193/steps/seed1/step_{ax}_indi",
    "pid": "indi_vs_pid/step_{ax}_pid",
}
AXES = {"roll": 0, "pitch": 1, "yaw": 2}
STEP_WIN = {"roll": (-0.5, 1.5), "pitch": (-0.5, 1.5), "yaw": (-0.5, 3.0)}


def topic(u, name):
    return next(d for d in u.data_list if d.name == name and d.multi_id == 0).data


def q2e(q):
    w, x, y, z = q.T
    return np.degrees(np.vstack([np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)),
                                 np.arcsin(np.clip(2 * (w * y - z * x), -1, 1)),
                                 np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))]).T)


def unwrap(a):
    return np.degrees(np.unwrap(np.radians(a)))


def zoh(t_src, v_src, t_dst):
    i = np.clip(np.searchsorted(t_src, t_dst, side="right") - 1, 0, len(t_src) - 1)
    return v_src[i]


def write(name, header, cols, note):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    np.savetxt(path, np.column_stack(cols), delimiter=",", header=",".join(header), comments="", fmt="%.5g")
    print("wrote", path, len(cols[0]), "rows,", os.path.getsize(path), "bytes;", note)


def extract_step(ctrl, ax):
    rel = STEP_RUNS[ctrl].format(ax=ax)
    u = ULog(os.path.join(RES, rel, "flight.ulg"))
    k = AXES[ax]
    att, asp = topic(u, "vehicle_attitude"), topic(u, "vehicle_attitude_setpoint")
    av, rsp = topic(u, "vehicle_angular_velocity"), topic(u, "vehicle_rates_setpoint")
    ta, a = att["timestamp"] * 1e-6, q2e(np.vstack([att[f"q[{i}]"] for i in range(4)]).T)[:, k]
    ts, s = asp["timestamp"] * 1e-6, q2e(np.vstack([asp[f"q_d[{i}]"] for i in range(4)]).T)[:, k]
    if ax == "yaw":
        a, s = unwrap(a), unwrap(s)
    tw, w = av["timestamp"] * 1e-6, np.degrees(av[f"xyz[{k}]"])
    tr, r = rsp["timestamp"] * 1e-6, np.degrees(rsp[ax])
    jump = np.nonzero(np.abs(np.diff(s)) > 1.0)[0][0]
    t_on = ts[jump + 1]
    pre = np.median(s[(ts > t_on - 1.5) & (ts < t_on)])
    t = np.arange(STEP_WIN[ax][0], STEP_WIN[ax][1] + 1e-9, 1 / FS)
    tt = t_on + t
    a_i = np.interp(tt, ta, a) - pre
    s_i = zoh(ts, s, tt) - pre
    w_i = np.interp(tt, tw, w)
    r_i = zoh(tr, r, tt)
    write(f"step_{ctrl}_{ax}.csv", ["t_s", "att_deg", "att_sp_deg", "rate_dps", "rate_sp_dps"],
          [t, a_i, s_i, w_i, r_i], f"{rel}/flight.ulg onset {t_on:.3f} s")


def extract_g3():
    # draw 3 (route B reference flights): pitch rate q, INDI and PID, same absolute log-time window
    base = "g3_routeB_s239/ref_s241/{c}_d3/run_003/flight.ulg"
    series = {}
    for c in ("indi", "pid"):
        u = ULog(os.path.join(RES, base.format(c=c)))
        av = topic(u, "vehicle_angular_velocity")
        series[c] = (av["timestamp"] * 1e-6, np.degrees(av["xyz[1]"]))
    # window: 8 s centred on the largest 1.5-3 Hz pitch-rate content of the INDI flight
    t, q = series["indi"]
    tg = np.arange(t[0], t[-1], 1 / FS)
    qg = np.interp(tg, t, q)
    n = int(FS)
    best, bi = 0, 0
    for i in range(0, len(tg) - 8 * n, n // 2):
        seg = qg[i:i + 8 * n]
        f = np.fft.rfftfreq(len(seg), 1 / FS)
        sp = np.abs(np.fft.rfft(seg - seg.mean())) * 2 / len(seg)
        m = sp[(f > 1.5) & (f < 3.0)].max()
        if m > best:
            best, bi = m, i
    t0 = tg[bi]
    tw = np.arange(0, 8, 1 / FS)
    cols = [tw] + [np.interp(t0 + tw, *series[c]) for c in ("indi", "pid")]
    write("g3_draw3_pitch_rate.csv", ["t_s", "q_indi_dps", "q_pid_dps"], cols,
          f"{base.format(c='indi')} and pid, window start {t0:.2f} s log time (same absolute window both)")


def extract_264():
    # draw 264: speed-1 re-fly pair, tilt and rates around the fault (log time = sim time)
    base = "g3_refly_s199/{c}_264/run_264/flight.ulg"
    cols, names = None, ["t_s"]
    tw = np.arange(57.5, 62.0, 1 / FS)
    out = [tw - 58.683]  # relative to the fault step (trigger 58.683 s, q26_264_s207/README.md)
    for c in ("indi", "pid"):
        u = ULog(os.path.join(RES, base.format(c=c)))
        att = topic(u, "vehicle_attitude")
        av = topic(u, "vehicle_angular_velocity")
        q = np.vstack([att[f"q[{i}]"] for i in range(4)]).T
        tilt = np.degrees(np.arccos(np.clip(1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2), -1, 1)))
        out.append(np.interp(tw, att["timestamp"] * 1e-6, tilt))
        out.append(np.interp(tw, av["timestamp"] * 1e-6, np.degrees(av["xyz[1]"])))
        names += [f"tilt_{c}_deg", f"q_{c}_dps"]
    write("g3_draw264_tilt.csv", names, out, base.format(c="{indi,pid}") + " window 57.5-62 s log time")


if __name__ == "__main__":
    what = sys.argv[1:] or ["steps", "g3"]
    if "steps" in what:
        for c in STEP_RUNS:
            for ax in AXES:
                extract_step(c, ax)
    if "g3" in what:
        extract_g3()
        extract_264()
