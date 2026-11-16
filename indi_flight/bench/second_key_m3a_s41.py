#!/usr/bin/env python3
"""Second-key M3a loop margins with variants.

Usage: second_key_m3a_s41.py <flight.ulg> <out.md> [primary_margins.txt]

Variant A  : full window (first..last inject != 0), direct sums, L = -Y/X.
Variant B1 : periods 2-3 only (window start + 10 s .. end), direct sums, L = -Y/X.
Variant B2 : three 10 s periods, coefficients per period (local time reference),
             averaged over periods, L = -(Y_avg/D_avg)/(X_avg/D_avg).
|D| is the single-sided excitation amplitude 2|D|/N; |X|/|D| is the coefficient ratio.
x = torque_sp[0] (u = c + d), y = torque_sp_pre_inject[0] (c).
"""
import ast
import re
import sys
from pathlib import Path

import numpy as np
from pyulog import ULog

PERIOD = 10.0


def field(ds, name):
    if name in ds.data:
        return np.asarray(ds.data[name], dtype=float)
    base, sep, idx = name.partition("[")
    if sep and base in ds.data:
        arr = np.asarray(ds.data[base], dtype=float)
        return arr[:, int(idx.rstrip("]"))] if arr.ndim == 2 else arr
    raise KeyError(f"{name} not found; available: {sorted(ds.data)}")


def coeffs(tt, xx, yy, dd, freqs):
    E = np.exp(-2j * np.pi * np.outer(freqs, tt))
    return E @ xx, E @ yy, E @ dd


def margins(freqs, L):
    mag_db = 20 * np.log10(np.abs(L))
    arg_deg = np.rad2deg(np.angle(L))
    ph = np.rad2deg(np.unwrap(np.deg2rad(arg_deg)))
    lf = np.log10(freqs)
    fc = pm = fg = gm = float("nan")
    down = np.flatnonzero((mag_db[:-1] >= 0) & (mag_db[1:] < 0))
    if down.size:
        i = down[0]
        a = mag_db[i] / (mag_db[i] - mag_db[i + 1])
        fc = 10 ** (lf[i] + a * (lf[i + 1] - lf[i]))
        pm = 180 + ph[i] + a * (ph[i + 1] - ph[i])
        for k in range(i + 1, len(freqs) - 1):
            if ph[k] > -180 >= ph[k + 1]:
                b = (ph[k] + 180) / (ph[k] - ph[k + 1])
                fg = 10 ** (lf[k] + b * (lf[k + 1] - lf[k]))
                gm = -(mag_db[k] + b * (mag_db[k + 1] - mag_db[k]))
                break
    return dict(mag_db=mag_db, arg_deg=arg_deg, fc=fc, pm=pm, fg=fg, gm=gm)


def read_primary(path):
    txt = path.read_text()

    def row(key):
        m = re.search(r"^" + re.escape(key) + r" (\[.*?\])", txt, re.M)
        return np.array(ast.literal_eval(m.group(1)), dtype=float)

    return dict(
        f=row("f"),
        mag_db=row("|L| dB"),
        arg_deg=row("arg deg"),
        pm=float(re.search(r'"pm_deg": ([-0-9.eE+]+)', txt).group(1)),
        gm=float(re.search(r'"gm_db": ([-0-9.eE+]+)', txt).group(1)),
        fc=float(re.search(r'"f_c": ([-0-9.eE+]+)', txt).group(1)),
    )


def section(title, desc, freqs, mg, damp, ratio, prim):
    lines = [title, "", desc, ""]
    if prim is None:
        lines += ["| f (Hz) | abs(L) dB | arg L deg | abs(D) | abs(X)/abs(D) |",
                  "|---:|---:|---:|---:|---:|"]
    else:
        lines += ["| f (Hz) | prim abs(L) dB | abs(L) dB | delta dB | prim arg deg | arg deg | delta deg | abs(D) | abs(X)/abs(D) | out of tol (<=20 Hz) |",
                  "|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--|"]
    nL = nA = 0
    for i, f in enumerate(freqs):
        g, p = mg["mag_db"][i], mg["arg_deg"][i]
        if prim is None:
            lines.append(f"| {f:.1f} | {g:.2f} | {p:.1f} | {damp[i]:.3g} | {ratio[i]:.3g} |")
            continue
        dg = g - prim["mag_db"][i]
        da = (p - prim["arg_deg"][i] + 180) % 360 - 180
        flags = []
        if f <= 20.0 + 1e-9:
            if abs(dg) > 0.5:
                flags.append("abs(L)")
                nL += 1
            if abs(da) > 3:
                flags.append("arg")
                nA += 1
        lines.append(
            f"| {f:.1f} | {prim['mag_db'][i]:.2f} | {g:.2f} | {dg:+.2f} | {prim['arg_deg'][i]:.1f} "
            f"| {p:.1f} | {da:+.1f} | {damp[i]:.3g} | {ratio[i]:.3g} | {' '.join(flags)} |")
    lines.append("")
    if prim is None:
        lines += [f"- PM {mg['pm']:.2f} deg, crossover {mg['fc']:.3f} Hz, GM {mg['gm']:.2f} dB at {mg['fg']:.3f} Hz", ""]
    else:
        dpm = mg["pm"] - prim["pm"]
        ok = nL == 0 and nA == 0 and abs(dpm) <= 2
        lines += [
            f"- PM: {mg['pm']:.2f} vs primary {prim['pm']:.2f} deg (delta {dpm:+.2f})",
            f"- Crossover: {mg['fc']:.3f} vs primary {prim['fc']:.3f} Hz",
            f"- GM: {mg['gm']:.2f} vs primary {prim['gm']:.2f} dB (delta {mg['gm'] - prim['gm']:+.2f})",
            f"- Bins out of tolerance (<=20 Hz): abs(L) {nL}, arg {nA}",
            f"- **Verdict: {'AGREE' if ok else 'DISAGREE'}**",
            "",
        ]
    return lines


def main():
    ulg_path, out_path = sys.argv[1], Path(sys.argv[2])
    prim = read_primary(Path(sys.argv[3])) if len(sys.argv) > 3 else None
    ds = ULog(ulg_path).get_dataset("indi_rate_status")
    t = field(ds, "timestamp_sample") * 1e-6
    d = field(ds, "inject[0]")
    x = field(ds, "torque_sp[0]")
    y = field(ds, "torque_sp_pre_inject[0]")
    nz = np.flatnonzero(d != 0)
    i0, i1 = nz[0], nz[-1]
    sl = slice(i0, i1 + 1)
    tw = t[sl] - t[i0]
    xw, yw, dw = x[sl], y[sl], d[sl]
    if not (np.all(np.isfinite(xw)) and np.all(np.isfinite(yw))):
        raise SystemExit("non-finite samples in window")
    freqs = np.round(10 ** (np.arange(18) / 10.0), 1)
    if prim is not None and not np.allclose(prim["f"], freqs, atol=1e-6):
        raise SystemExit("primary frequency grid differs")

    # Variant A: full window.
    XA, YA, DA = coeffs(tw, xw, yw, dw, freqs)
    NA = tw.size
    LA = -YA / XA

    # Variant B1: periods 2-3 only.
    mB = tw >= PERIOD - 1e-6
    XB1, YB1, DB1 = coeffs(tw[mB], xw[mB], yw[mB], dw[mB], freqs)
    NB1 = int(mB.sum())
    LB1 = -YB1 / XB1

    # Variant B2: per-period coefficients (local time), averaged, then ratio.
    p = np.minimum((tw / PERIOD).astype(int), 2)
    Xs, Ys, Ds, counts = [], [], [], []
    for k in range(3):
        m = p == k
        Xk, Yk, Dk = coeffs(tw[m] - k * PERIOD, xw[m], yw[m], dw[m], freqs)
        Xs.append(Xk)
        Ys.append(Yk)
        Ds.append(Dk)
        counts.append(int(m.sum()))
    Xa = np.mean(Xs, axis=0)
    Ya = np.mean(Ys, axis=0)
    Da = np.mean(Ds, axis=0)
    LB2 = -(Ya / Da) / (Xa / Da)
    NB2 = float(np.mean(counts))

    lines = [f"### Run `{ulg_path}`", "",
             f"- Full window {t[i0]:.3f} to {t[i1]:.3f} s, {NA} samples", ""]
    lines += section("#### Variant A signal levels (full window, current method)",
                     f"Full window, {NA} samples. Margins as in the main table.",
                     freqs, margins(freqs, LA), 2 * np.abs(DA) / NA,
                     np.abs(XA) / np.abs(DA), None)
    lines += section("#### Variant B1: periods 2-3, direct sums, L = -Y/X",
                     f"Window {t[i0] + PERIOD:.3f} to {t[i1]:.3f} s, {NB1} samples",
                     freqs, margins(freqs, LB1), 2 * np.abs(DB1) / NB1,
                     np.abs(XB1) / np.abs(DB1), prim)
    lines += section("#### Variant B2: per-period coefficients averaged, L = -(Y_avg/D_avg)/(X_avg/D_avg)",
                     f"Periods 1-3 (10 s each), samples per period {counts}",
                     freqs, margins(freqs, LB2), 2 * np.abs(Da) / NB2,
                     np.abs(Xa) / np.abs(Da), prim)
    text = "\n".join(lines) + "\n"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
