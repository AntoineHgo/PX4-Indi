#!/usr/bin/env python3
"""S64 G4 pre-look (not a gate metric): noise carried by the setpoint lead term c * r_dot / G1 and motor effort.

Usage: rdot_effort_s64.py OUT.md FLIGHT_DIR...   (FLIGHT_DIR holds flight.ulg)
       rdot_effort_s64.py --selftest
Window: airborne cycles of indi_rate_status (vehicle_land_detected not landed / maybe_landed, held), trimmed 3 s at both ends, timestamp_sample.
Per axis: RMS of rate_sp_dot (rad/s^2); RMS of the lead torque term c*r_dot/G1 (normalised torque); high-frequency
RMS (deviation from a 0.25 s centred boxcar mean, i.e. content above ~4 Hz) of that term and of torque_sp.
Motors: actuator_motors control[0..3] HF RMS (same boxcar) averaged over motors, and esc_status rpm HF RMS.
"""
import sys
import numpy as np


def hf_rms(t, x, width_s=0.25):
    """RMS of x minus its centred boxcar mean of width_s (uniformly resampled at the median dt)."""
    dt = float(np.median(np.diff(t)))
    tg = np.arange(t[0], t[-1], dt)
    xg = np.interp(tg, t, x)
    n = max(1, int(round(width_s / dt)))
    m = np.convolve(xg, np.ones(n) / n, mode="same")
    v = slice(n, len(xg) - n)
    return float(np.sqrt(np.mean((xg[v] - m[v]) ** 2)))


def rms(x):
    return float(np.sqrt(np.mean(np.asarray(x) ** 2)))


def selftest():
    t = np.arange(0, 10, 1 / 800.)
    a = 0.3
    x = 5.0 + 0.2 * t + a * np.sin(2 * np.pi * 40 * t)  # offset + ramp removed, 40 Hz tone kept
    got = hf_rms(t, x)
    assert abs(got - a / np.sqrt(2)) < 0.01 * a, got
    slow = 5.0 + 0.3 * np.sin(2 * np.pi * 0.5 * t)  # 0.5 Hz: mostly removed
    assert hf_rms(t, slow) < 0.02, hf_rms(t, slow)
    print("selftest OK")


def analyse(d):
    from pyulog import ULog
    ul = ULog(d + "/flight.ulg", ["indi_rate_status", "actuator_motors", "esc_status", "vehicle_land_detected"])
    g = {x.name: x.data for x in ul.data_list}
    s = g["indi_rate_status"]
    t = s["timestamp_sample"] * 1e-6
    ld = g["vehicle_land_detected"]
    tl = ld["timestamp"] * 1e-6
    k = np.clip(np.searchsorted(tl, t, side="right") - 1, 0, len(tl) - 1)
    air = (ld["landed"][k] == 0) & (ld["maybe_landed"][k] == 0) & (t >= tl[0])  # works with MC_INDI_LEAD 0
    ta = t[air]
    t0, t1 = ta[0] + 3, ta[-1] - 3
    w = (t >= t0) & (t <= t1) & air
    p = ul.initial_parameters
    g1 = [p["MC_INDI_G1_R"], p["MC_INDI_G1_P"], p["MC_INDI_G1_Y"]]
    row = {"dur": t1 - t0}
    for i, ax in enumerate("rpy"):
        rd = s[f"rate_sp_dot[{i}]"][w]
        term = s[f"lead_gain[{i}]"][w] * rd / g1[i]
        row[f"rd_{ax}"] = rms(rd)
        row[f"term_{ax}"] = rms(term)
        row[f"termhf_{ax}"] = hf_rms(t[w], term)
        row[f"tsphf_{ax}"] = hf_rms(t[w], s[f"torque_sp[{i}]"][w])
    m = g["actuator_motors"]
    tm = m["timestamp"] * 1e-6
    wm = (tm >= t0) & (tm <= t1)
    row["mot_hf"] = float(np.mean([hf_rms(tm[wm], m[f"control[{k}]"][wm]) for k in range(4)]))
    row["mot_mean"] = float(np.mean([np.mean(m[f"control[{k}]"][wm]) for k in range(4)]))
    e = g["esc_status"]
    te = e["timestamp"] * 1e-6
    we = (te >= t0) & (te <= t1)
    row["rpm_hf"] = float(np.mean([hf_rms(te[we], e[f"esc[{k}].esc_rpm"][we].astype(float)) for k in range(4)]))
    return row


def main():
    if sys.argv[1] == "--selftest":
        return selftest()
    out, dirs = sys.argv[1], sys.argv[2:]
    cols = ["dur", "rd_r", "rd_p", "rd_y", "term_r", "term_p", "term_y", "termhf_r", "termhf_p", "termhf_y",
            "tsphf_r", "tsphf_p", "tsphf_y", "mot_hf", "mot_mean", "rpm_hf"]
    lines = ["| flight | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
    for d in dirs:
        r = analyse(d)
        lines.append(f"| {d.rstrip('/').split('results/')[-1]} | " + " | ".join(f"{r[c]:.4g}" for c in cols) + " |")
    open(out, "w").write(__doc__.split("\n\n")[0] + "\n\n" + "\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
