#!/usr/bin/env python3
"""Independent (second-key) check of the A-31 disturbance wrench.

Checks, per run (payload_add, com_shift):
  1. Hover thrust ratio from ESC rotor speeds (sum omega^2, pre vs late window).
  2. Rotor-produced roll/pitch torque change (k_f * omega^2 * arm) vs applied torque.
  3. disturbance.csv sim-time sampling: gaps and duplicates.

Read-only on inputs. Output: stdout only.
"""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from pyulog import ULog

REPO = Path("/home/ahugo/Documents/Drotek/Codes/PX4-Indi")
RUN = REPO / "indi_flight/results/a31_fix_s67"
SDF_ARM = REPO / "indi_flight/sim/models/quad5in_base/model.sdf"  # rotor positions
SDF_KF = REPO / "indi_flight/sim/models/quad5in/model.sdf"        # motorConstant
G = 9.81
PHYS_STEP = 0.004
PRE = (-5.0, 0.0)      # s relative to onset, hover window
LATE = (20.0, 25.0)    # s relative to onset, profile is 30 s long


def sdf_info(path):
    root = ET.parse(path).getroot()
    rotors = {}
    for link in root.iter("link"):
        name = link.get("name", "")
        if name.startswith("rotor_") and name[6:].isdigit():
            x, y, z = map(float, link.find("pose").text.split()[:3])
            rotors[int(name[6:])] = (x, y, z)
    masses = [float(e.text) for e in root.iter("mass")]
    kf = [float(e.text) for e in root.iter("motorConstant")]
    return rotors, masses, kf


def window(t, onset, rel):
    return (t >= onset + rel[0]) & (t < onset + rel[1])


def load_esc(ulg_path):
    u = ULog(str(ulg_path))
    d = next(x for x in u.data_list if x.name == "esc_status")
    t = d.data["timestamp"] * 1e-6  # PX4 clock, seconds
    rpm = np.stack([d.data[f"esc[{i}].esc_rpm"] for i in range(4)], axis=1).astype(float)
    return t, rpm * 2.0 * np.pi / 60.0  # rad/s, shape (N, 4)


def load_csv(path):
    rows = np.genfromtxt(path, delimiter=",", names=True)
    return rows


def run_case(name, onset, rotors, m, kf_sdf):
    d = RUN / name
    t, om = load_esc(d / "flight.ulg")
    w2 = om ** 2
    s = w2.sum(axis=1)
    pre = window(t, onset, PRE)
    late = window(t, onset, LATE)
    print(f"== {name}  onset (PX4 clock) = {onset:.4f} s")
    print(f"   esc samples: {len(t)}, pre {pre.sum()}, late {late.sum()}")
    print(f"   mean rpm pre: {np.mean(om[pre]) * 60 / (2 * np.pi):.0f}")

    s_pre = s[pre].mean()
    s_late = s[late].mean()
    ratio = s_late / s_pre
    csv = load_csv(d / "disturbance.csv")
    active = (csv["fx"] != 0) | (csv["fy"] != 0) | (csv["fz"] != 0) | \
             (csv["tx"] != 0) | (csv["ty"] != 0) | (csv["tz"] != 0)
    fz_applied = csv["fz"][active]
    fz_mag = float(np.abs(fz_applied).max()) if fz_applied.size else 0.0
    applied_t = np.array([csv["tx"][active].mean(), csv["ty"][active].mean(),
                          csv["tz"][active].mean()]) if active.any() else np.zeros(3)
    print(f"   sum(omega^2) pre  = {s_pre:.4e}  late = {s_late:.4e}")
    print(f"   ratio late/pre   = {ratio:.4f}")
    print(f"   applied Fz (csv) = {fz_mag:.4f} N  -> |Fz|/(mg) = {fz_mag / (m * G):.4f}")
    print(f"   expected ratio 1+|Fz|/(mg) = {1 + fz_mag / (m * G):.4f}")

    # settling profile in 2.5 s bins (ratio vs pre mean)
    edges = np.arange(-5.0, 31.0, 2.5)
    line = []
    for a, b in zip(edges[:-1], edges[1:]):
        mm = (t >= onset + a) & (t < onset + b)
        if mm.any():
            line.append(f"[{a:+.1f},{b:+.1f}):{s[mm].mean() / s_pre:.3f}")
    print("   settling (ratio to pre):", " ".join(line))

    # rotor-produced torques, k_f * omega^2 * arm
    pos = np.array([rotors[i][:2] for i in range(4)])  # (x, y) per rotor
    kf_hover = m * G / s_pre  # k_f implied by hover thrust balance
    out = {"ratio": ratio, "fz_mag": fz_mag, "kf_hover": kf_hover, "kf_sdf": kf_sdf}
    for label, kf in (("sdf", kf_sdf), ("hover", kf_hover)):
        def torque(win):
            f = kf * w2[win].mean(axis=0)  # thrust per rotor
            tx = float(np.sum(pos[:, 1] * f))
            ty = float(-np.sum(pos[:, 0] * f))
            return np.array([tx, ty])
        tp = torque(pre)
        tl = torque(late)
        dt = tl - tp
        print(f"   k_f={label}:{kf:.4e}  rotor tau pre=({tp[0]:+.5f},{tp[1]:+.5f}) "
              f"late=({tl[0]:+.5f},{tl[1]:+.5f})  delta=({dt[0]:+.5f},{dt[1]:+.5f}) N m")
        out[label] = {"tau_pre": tp.tolist(), "tau_late": tl.tolist(), "delta": dt.tolist()}
    print(f"   applied torque (csv mean over profile) = "
          f"({applied_t[0]:+.5f},{applied_t[1]:+.5f},{applied_t[2]:+.5f}) N m")
    out["applied_torque"] = applied_t.tolist()
    return out


def csv_check(name):
    csv = load_csv(RUN / name / "disturbance.csv")
    t = csv["sim_time_s"]
    dt = np.diff(t)
    print(f"== csv {name}: rows {len(t)}, span {t[-1] - t[0]:.4f} s")
    print(f"   duplicates (dt==0): {int((dt == 0).sum())}, non-monotonic: {int((dt < 0).sum())}")
    print(f"   dt min/median/max = {dt.min():.6f} / {np.median(dt):.6f} / {dt.max():.6f} s "
          f"(max at t={t[dt.argmax()]:.4f})")
    print(f"   max gap / physics step ({PHYS_STEP} s) = {dt.max() / PHYS_STEP:.3f}; "
          f"intervals > 1.5 step: {int((dt > 1.5 * PHYS_STEP).sum())}")


def main():
    rotors, masses, _ = sdf_info(SDF_ARM)
    _, _, kf_list = sdf_info(SDF_KF)
    m = 0.61  # airframe mass from PX4 log / task spec (0.566 + 4 x 0.011)
    kf_sdf = kf_list[0]
    print(f"SDF rotor positions (quad5in_base): {rotors}")
    print(f"SDF masses (quad5in_base): {masses} sum={sum(masses):.3f}; motorConstant (quad5in): {kf_sdf}")

    onset_pay = json.loads((RUN / "payload_add/disturbance_trigger.json").read_text())["onset_px4_s"]
    onset_com = json.loads((RUN / "com_shift/disturbance_trigger.json").read_text())["onset_px4_s"]

    res = {}
    res["payload_add"] = run_case("payload_add", onset_pay, rotors, m, kf_sdf)
    res["com_shift"] = run_case("com_shift", onset_com, rotors, m, kf_sdf)
    csv_check("payload_add")
    csv_check("com_shift")
    print("JSON", json.dumps(res))


if __name__ == "__main__":
    main()
