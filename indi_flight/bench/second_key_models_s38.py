#!/usr/bin/env python3
"""T79 second key: independent continuous-time margin models (stage-2 S38).

Usage: python3 indi_flight/bench/second_key_models_s38.py OUT.md
Writes the numbers to OUT.md and prints them. Continuous time, numpy only.
Models follow indi_flight/design/stage2_margins_s35.md sections 4.1, 4.2 and 7.
"""
import sys
import numpy as np

FS = 800.0
T = 1.0 / FS
K = 20.0                  # INDI rate gain, 1/s
G1 = 320.0                # rad/s^2 per unit normalised torque
TAU_R = 0.033             # real actuator lag (quad5in model), s
TAU_M = 0.02              # model actuator lag (MC_INDI_ACT_TC default), s
D_M = T                   # model chain delay: one sample (task spec)
FW_HZ = 40.0              # 2nd-order Butterworth gyro LPF
ALPHA_HZ = 20.0           # 1st-order LPF: H chain and PID D term
KP, KI, KD = 0.03, 0.06, 0.0006
W = 2 * np.pi * np.logspace(np.log10(0.1), np.log10(400.0), 40000)  # rad/s
S = 1j * W


def fw(s):
    wn = 2 * np.pi * FW_HZ
    return wn**2 / (s**2 + np.sqrt(2) * wn * s + wn**2)


def lp1(s, fc_hz):
    return 1.0 / (1.0 + s / (2 * np.pi * fc_hz))


def a_r(s):
    return np.exp(-s * T / 2) / (1.0 + TAU_R * s)


def a_m(s):
    return np.exp(-s * D_M) / (1.0 + TAU_M * s)


def h_chain(s):
    # H = F_w * alpha(20 Hz). The note's derivative (s) and the 1/s of the
    # rate chain cancel in the mismatch term, so H is dimensionless, ~1 at DC.
    return fw(s) * lp1(s, ALPHA_HZ)


def L_indi(s, g=1.0, model_scale=None):
    ar = a_r(s)
    am = a_m(s) if model_scale is None else model_scale * ar
    return g * (K / s) * fw(s) * ar + h_chain(s) * (g * ar - am)


def L_pid(s):
    ar = a_r(s)
    return (G1 * (KP / s + KI / s**2) * ar * fw(s)
            + KD * G1 * ar * fw(s) * lp1(s, ALPHA_HZ))


def cross(y, level):
    """Angular frequencies (rad/s) where y - level changes sign (log-interpolated)."""
    d = y - level
    i = np.where(d[:-1] * d[1:] < 0)[0]
    t = d[i] / (d[i] - d[i + 1])
    lw = np.log10(W[i]) + t * (np.log10(W[i + 1]) - np.log10(W[i]))
    return 10 ** lw


def at(w, y):
    return np.interp(np.log10(w), np.log10(W), y)


def margins(L):
    mag = 20 * np.log10(np.abs(L))
    ph = np.degrees(np.unwrap(np.angle(L)))
    wc = cross(mag, 0.0)
    pm = at(wc, ph) + 180.0
    dm_ms = np.radians(pm) / wc * 1e3
    wp = np.concatenate([cross(ph, lv) for lv in (-180.0, -540.0, -900.0)])
    gm = -at(wp, mag)
    return dict(fc=wc / (2 * np.pi), pm=pm, dm_ms=dm_ms, fp=wp / (2 * np.pi), gm=gm)


def fmt(a, nd=2):
    return ", ".join(f"{v:.{nd}f}" for v in a) if len(a) else "none"


def main():
    out = sys.argv[1]
    mi = margins(L_indi(S))
    mp = margins(L_pid(S))
    lines = [
        "# Second key T79: continuous-time margins (script output)",
        "",
        f"Grid 0.1-400 Hz, {W.size} log points, T = {T * 1e3:.4f} ms (model delays only).",
        "",
        "| Model | fc (Hz) | PM (deg) | DM (ms) | fp (Hz) | GM (dB) |",
        "|---|---|---|---|---|---|",
    ]
    for name, m in (("INDI model-only", mi), ("PID roll", mp)):
        lines.append(f"| {name} | {fmt(m['fc'])} | {fmt(m['pm'])} | {fmt(m['dm_ms'])} "
                     f"| {fmt(m['fp'])} | {fmt(m['gm'])} |")
    lines.append("")
    for name, m in (("INDI model-only", mi), ("PID roll", mp)):
        pm_w = m["pm"].min() if m["pm"].size else float("nan")
        dm_w = m["dm_ms"].min() if m["dm_ms"].size else float("nan")
        gm_w = m["gm"].min() if m["gm"].size else float("inf")
        lines.append(f"Worst {name}: PM {pm_w:.2f} deg, DM {dm_w:.2f} ms, GM {gm_w:.2f} dB")
    lines.append("")
    lines.append("Reduction check: A_m = eta A_r, g = eta -> L equals eta (K/s) F_w A_r")
    for eta in (1.0, 0.5, 0.25):
        ref = eta * (K / S) * fw(S) * a_r(S)
        got = L_indi(S, g=eta, model_scale=eta)
        rel = np.max(np.abs(got - ref)) / np.max(np.abs(ref))
        lines.append(f"  eta {eta:.2f}: max relative error {rel:.3e}")
    text = "\n".join(lines) + "\n"
    with open(out, "w") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main()
