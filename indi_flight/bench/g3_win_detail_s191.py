#!/usr/bin/env python3
"""S191: per-window table of the q line detector for key 1 (g3_checks) and key 2 (g3_checks_key2), plus a wide-band (0.5-6 Hz) peak
for each window, to show where a line sits relative to the 2.0 Hz band edge. Needs scipy (key 1): run in the px4-indi-sim image.
Usage: g3_win_detail_s191.py RESULTS_RUN_DIR  [t_lo t_hi, scorer-relative seconds for key 1 / grid time for key 2: printed raw]"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def table(x, fs, t_start, band=(2.0, 40.0), rms_hz=None, win=4.0, step=1.0):
    """[(t_start_window, f_peak_band, ratio, rms_dps(+-2 bins), f_peak_wide(0.5-6Hz), amp_wide_rms)] with the scorer's Hann periodogram"""
    from scipy.signal import periodogram
    n, st = int(round(win * fs)), int(round(step * fs)); out = []
    for s in range(0, len(x) - n + 1, st):
        f, P = periodogram(x[s:s + n], fs, window="hann", detrend="constant", scaling="density")
        b = (f >= band[0]) & (f <= band[1]); k = int(np.argmax(P[b])); kk = np.flatnonzero(b)[k]
        wd = (f >= 0.5) & (f <= 6.0); kw = np.flatnonzero(wd)[int(np.argmax(P[wd]))]
        out.append((t_start + s / fs, float(f[kk]), float(P[kk] / np.median(P[b])), float(np.sqrt(P[max(kk - 2, 0):kk + 3].sum() * (f[1] - f[0]))),
                    float(f[kw]), float(np.sqrt(P[max(kw - 2, 0):kw + 3].sum() * (f[1] - f[0])))))
    return out

def main():
    import g3_checks as k1, g3_checks_key2 as k2
    d = sys.argv[1]; r = json.load(open(os.path.join(d, "g3_checks.json")))
    ta, te = r["airborne"]
    from pyulog import ULog
    u = ULog(os.path.join(d, "flight.ulg"), ["sim_ground_truth"]); g = u.get_dataset("sim_ground_truth").data
    st = u.start_timestamp; tt = (g["timestamp_sample" if "timestamp_sample" in g else "timestamp"].astype(np.int64) - st) * 1e-6
    o = np.argsort(tt, kind="stable"); tt = tt[o]; q = np.degrees(g["angular_velocity[1]"][o].astype(float))
    from g4_metrics import uniform
    a = (tt >= ta) & (tt <= te); tg, wg, fs = uniform(tt[a], np.stack([q[a]] * 3, 1), ta, te)
    print("KEY1 windows (start s rel ulog start, f_band, ratio, rms_dps, f_wide, rms_wide); flagged = ratio>20 & rms>=5")
    for w in table(wg[1], fs, float(tg[0])):
        if w[3] > 0.8 or w[5] > 1.5: print("  %.1f f=%.2f ratio=%.0f rms=%.1f %s | wide f=%.2f rms=%.1f" % (w[0], w[1], w[2], w[3], "FLAG" if w[2] > 20 and w[3] >= 5 else "", w[4], w[5]))
    # key 2: truth on absolute clock, mask = scorer's analyse mask unknown here; use airborne span of key 2 json
    j2 = json.load(open(os.path.join(os.path.dirname(d), "key2", os.path.basename(d) + ".json")))
    sa, sb = j2["item1_loc"]["span_s"]
    ta2 = tt + st * 1e-6; m2 = (ta2 >= sa) & (ta2 <= sb)
    tg2, g2 = k2.grid(ta2[m2], np.stack([q[m2]] * 3, 1))
    print("KEY2 windows (start s rel ulog start = abs - %.2f); flagged = ratio>20 & rms>5, 3 consecutive within 10%%" % (st * 1e-6))
    for w in table(g2[:, 1], k2.FS, float(tg2[0])):
        if w[3] > 0.8 or w[5] > 1.5: print("  %.1f f=%.2f ratio=%.0f rms=%.1f %s | wide f=%.2f rms=%.1f" % (w[0] - st * 1e-6, w[1], w[2], w[3], "FLAG" if w[2] > 20 and w[3] > 5 else "", w[4], w[5]))
main()
