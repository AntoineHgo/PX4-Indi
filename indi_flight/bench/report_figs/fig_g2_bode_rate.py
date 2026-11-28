#!/usr/bin/env python3
"""Measured open-loop frequency response of the roll rate loop (Bode and Nichols) with its margins."""
import numpy as np

import data_g2
import style
from style import plt, INDIBLUE, INDIORANGE, INDIGREY


def wrap(a):
    """Phase in (-360, 0] so the -180 deg line is crossed once."""
    a = np.asarray(a, float)
    return np.where(a > 0, a - 360.0, a)


def main():
    r = data_g2.rate_spot()
    f, mag, ph = np.array(r["f"]), np.array(r["mag_db"]), wrap(r["arg_deg"])
    fig = plt.figure(figsize=(style.FULL, 2.3))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.25, 1], hspace=0.12, wspace=0.32)
    a1 = fig.add_subplot(gs[0, 0])
    a2 = fig.add_subplot(gs[1, 0], sharex=a1)
    a3 = fig.add_subplot(gs[:, 1])
    a1.semilogx(f, mag, "o-", color=INDIBLUE, ms=3)
    a1.axhline(0, color=INDIGREY, lw=0.6)
    a1.axvline(r["f_c"], color=INDIGREY, lw=0.6, ls=":")
    a1.axvline(r["f_gm"], color=INDIGREY, lw=0.6, ls=":")
    a1.set_ylabel("$|L|$ (dB)")
    plt.setp(a1.get_xticklabels(), visible=False)
    a2.semilogx(f, ph, "o-", color=INDIBLUE, ms=3)
    a2.axhline(-180, color=INDIORANGE, lw=1.0, ls="--")
    a2.axvline(r["f_c"], color=INDIGREY, lw=0.6, ls=":")
    a2.axvline(r["f_gm"], color=INDIGREY, lw=0.6, ls=":")
    a2.annotate(f"PM {r['pm']:.1f} deg", xy=(r["f_c"], -180 + r["pm"]), xytext=(1.0, -232), fontsize=7.5,
                arrowprops=dict(arrowstyle="-", lw=0.5, color=INDIGREY))
    a2.set_ylabel("$\\arg L$ (deg)")
    a2.set_xlabel("Frequency (Hz)")
    a2.set_ylim(-255, -70)
    # Nichols
    a3.plot(ph, mag, "o-", color=INDIBLUE, ms=3)
    a3.plot([-180], [0], "+", color=INDIORANGE, ms=9, mew=1.2)
    a3.axhline(0, color=INDIGREY, lw=0.6)
    a3.axvline(-180, color=INDIORANGE, lw=0.8, ls="--")
    a3.annotate(f"GM {r['gm']:.1f} dB", xy=(-180, -r["gm"]), xytext=(-168, -r["gm"] - 3), fontsize=7.5,
                arrowprops=dict(arrowstyle="-", lw=0.5, color=INDIGREY))
    a3.set_xlabel("$\\arg L$ (deg)")
    a3.set_ylabel("$|L|$ (dB)")
    style.panel_label(a1, "(a)")
    style.panel_label(a3, "(b)")
    style.save(fig, "g2_bode_rate")


if __name__ == "__main__":
    main()
