#!/usr/bin/env python3
"""Compare attitude and position excursions after disturbance onset: old (double wrench,
g15_dist_s66) vs new (single wrench, a31_fix_s67) runs of the same profiles.

Excursion = peak |value - pre-onset reference| inside [onset, profile_end + 3 s];
reference = mean over the 2 s before onset. Yaw is wrapped to [-pi, pi].
Writes a markdown table to a31_fix_s67/others.md and prints it.
"""
import math
import re
import sys
from pathlib import Path

import numpy as np
import pyulog

RES = Path("/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results")
OLD = RES / "g15_dist_s66"
NEW = RES / "a31_fix_s67"
PROFILES = ["torque_steps", "gust_x", "gust_diag"]


def load_ulg(path):
    u = pyulog.ULog(str(path))
    out = {}
    for name in ("vehicle_attitude", "vehicle_local_position"):
        d = next(x for x in u.data_list if x.name == name)
        out[name] = d.data
    return out


def euler(att):
    w, x, y, z = att["q[0]"], att["q[1]"], att["q[2]"], att["q[3]"]
    roll = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = np.arcsin(np.clip(2 * (w * y - z * x), -1, 1))
    yaw = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return roll, pitch, yaw


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def run_stats(d):
    trig = __import__("json").loads((d / "disturbance_trigger.json").read_text())
    onset = float(trig["onset_px4_s"])
    log = (d / "disturbance.log").read_text()
    m = re.search(r"profile ended at sim ([\d.]+)", log)
    end = float(m.group(1)) - 0 if m else onset + 15.0
    # gz sim time vs px4 time offset is not needed: profile end is reported in gz sim
    # time, onset in px4 time; the difference (end - onset) is the profile duration.
    t_end = onset + (end - float(re.search(r"onset gz sim time ([\d.]+)", log).group(1)))
    ulg = load_ulg(d / "flight.ulg")
    att, pos = ulg["vehicle_attitude"], ulg["vehicle_local_position"]
    ta = att["timestamp"] * 1e-6
    tp = pos["timestamp"] * 1e-6
    roll, pitch, yaw = euler(att)

    def window(t, lo, hi):
        return (t >= lo) & (t <= hi)

    pre_a = window(ta, onset - 2, onset)
    post_a = window(ta, onset, t_end + 3)
    pre_p = window(tp, onset - 2, onset)
    post_p = window(tp, onset, t_end + 3)
    if not pre_a.any() or not post_a.any() or not pre_p.any() or not post_p.any():
        raise RuntimeError(f"{d}: onset {onset} outside ulog range {ta[0]:.1f}-{ta[-1]:.1f}")

    exc = {}
    for label, sig in (("roll", roll), ("pitch", pitch), ("yaw", yaw)):
        ref = np.mean(sig[pre_a])
        dev = wrap(sig[post_a] - ref)
        exc[label] = math.degrees(np.max(np.abs(dev)))
    px = pos["x"]
    py = pos["y"]
    pz = pos["z"]
    ref = np.array([np.mean(px[pre_p]), np.mean(py[pre_p]), np.mean(pz[pre_p])])
    dxy = np.hypot(px[post_p] - ref[0], py[post_p] - ref[1])
    dz = np.abs(pz[post_p] - ref[2])
    exc["pos_xy_m"] = float(np.max(dxy))
    exc["pos_z_m"] = float(np.max(dz))
    exc["onset"] = onset
    exc["end"] = t_end
    return exc


def rc_of(name):
    for line in (NEW / "done.txt").read_text().splitlines():
        if line.startswith(name + " rc="):
            return line.split("rc=")[1]
    return "?"


def main():
    rows = []
    hdr = ("| profile | rc | runtime add NO | metrics.json | axis | old | new | new/old |\n"
           "|---|---|---|---|---|---|---|---|")
    rows.append(hdr)
    failed = []
    for p in PROFILES:
        new_dir, old_dir = NEW / p, OLD / p
        rc = rc_of(p)
        log = (new_dir / "disturbance.log").read_text()
        no = "yes" if "runtime add NO" in log else "no"
        met = "yes" if (new_dir / "metrics.json").exists() else "NO"
        try:
            o = run_stats(old_dir)
            n = run_stats(new_dir)
        except Exception as e:  # keep going, report the failure
            failed.append(f"{p}: {e}")
            rows.append(f"| {p} | {rc} | {no} | {met} | - | - | - | - |")
            continue
        for ax in ("roll", "pitch", "yaw", "pos_xy_m", "pos_z_m"):
            unit = "m" if ax.startswith("pos") else "deg"
            ratio = n[ax] / o[ax] if o[ax] > 0 else float("nan")
            rows.append(f"| {p} | {rc} | {no} | {met} | {ax} ({unit}) | "
                        f"{o[ax]:.3f} | {n[ax]:.3f} | {ratio:.2f} |")
        rows[-1] = rows[-1]  # no-op, keeps structure readable
    text = "\n".join(rows) + "\n"
    if failed:
        text += "\nFailures:\n" + "\n".join(f"- {f}" for f in failed) + "\n"
    (NEW / "others.md").write_text(
        "# A-31 fix re-fly (S67): excursion old (double wrench) vs new (single wrench)\n\n"
        "Excursion = peak deviation from the 2 s pre-onset reference, from onset to profile end + 3 s.\n\n"
        + text)
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
