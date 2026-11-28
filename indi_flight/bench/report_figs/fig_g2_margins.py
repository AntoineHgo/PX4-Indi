#!/usr/bin/env python3
"""G2 stability margins per loop against the thresholds (phase, gain and delay margin)."""
import numpy as np

import data_g2
import style
from style import plt, INDIBLUE, INDIORANGE, INDILIGHT, INDIGREY

PM_MIN, GM_MIN = 45.0, 6.0

LOOPS = [  # label, selector
    ("Rate, roll", "rate"),
    ("Attitude, pitch", "att"),
    ("Velocity/position, xy", (0, (1, 2))),
    ("Velocity/position, z", (0, (3,))),
    ("Acceleration, xy", (1, (1, 2))),
    ("Acceleration, z", (1, (3,))),
]


def collect():
    """Return list of (row, rate_hz, pm, gm|None, dm_ms)."""
    out = []
    r = data_g2.rate_spot()
    out.append((0, 800, r["pm"], r["gm"], r["dm_ms"]))
    a = data_g2.att_spot()
    out.append((1, 400, a["pm"], a["gm"], a["dm_ms"]))
    cells = data_g2.outer_cells()
    for i, (_, sel) in enumerate(LOOPS):
        if isinstance(sel, tuple):
            pt, axs = sel
            for c in cells.values():
                if c["pt"] == pt and c["ax"] in axs:
                    out.append((i, c["rate"], c["pm"], c["gm"], c["dm_ms"]))
    return out


def main():
    pts = collect()
    fig, axs = plt.subplots(1, 3, figsize=(style.FULL, 2.3), sharey=True)
    n = len(LOOPS)
    rng = np.random.default_rng(1)
    for k, ax in enumerate(axs):
        ax.set_ylim(n - 0.5, -0.5)
        ax.set_yticks(range(n))
        ax.set_yticklabels([l for l, _ in LOOPS])
        ax.grid(axis="y", visible=False)
        for row, rate, pm, gm, dm in pts:
            v = (pm, gm, dm)[k]
            if v is None:
                continue
            y = row + rng.uniform(-0.18, 0.18)
            if rate == 800:
                ax.plot(v, y, "o", mfc="white", mec=INDIBLUE, mew=0.9, ms=4.2)
            else:
                ax.plot(v, y, "o", color=INDIBLUE, ms=4.2)
    ax = axs[0]
    ax.axvline(PM_MIN, color=INDIORANGE, lw=1.0, ls="--")
    ax.axvspan(30, PM_MIN, color=INDIORANGE, alpha=0.10, lw=0)
    ax.set_xlim(30, 80)
    ax.set_xlabel("Phase margin (deg)")
    ax = axs[1]
    ax.axvline(GM_MIN, color=INDIORANGE, lw=1.0, ls="--")
    ax.axvspan(0, GM_MIN, color=INDIORANGE, alpha=0.10, lw=0)
    ax.set_xlim(0, 30)
    ax.set_xlabel("Gain margin (dB)")
    for row in (3, 5):  # no -180 deg crossing in the band: no gain margin
        ax.text(6.8, row, "no crossing", fontsize=7, color=INDIGREY, va="center", style="italic")
    ax = axs[2]
    ax.set_xscale("log")
    for per_ms in (2 / 800 * 1e3, 2 / 400 * 1e3):
        ax.axvline(per_ms, color=INDIORANGE, lw=1.0, ls="--")
    ax.axvspan(1, 2 / 800 * 1e3, color=INDIORANGE, alpha=0.10, lw=0)
    ax.set_xlim(1, 1000)
    ax.set_xlabel("Delay margin (ms)")
    # legend
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="o", ls="", color=INDIBLUE, ms=4.2, label="400 Hz"),
         Line2D([], [], marker="o", ls="", mfc="white", mec=INDIBLUE, mew=0.9, ms=4.2, label="800 Hz"),
         Line2D([], [], color=INDIORANGE, ls="--", lw=1.0, label="threshold")]
    fig.tight_layout(w_pad=0.8, rect=(0, 0, 1, 0.92))
    fig.legend(handles=h, loc="upper center", ncol=3, fontsize=7.5, handletextpad=0.3, columnspacing=1.5)
    style.save(fig, "g2_margins")


if __name__ == "__main__":
    main()
