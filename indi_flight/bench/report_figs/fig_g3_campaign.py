#!/usr/bin/env python3
"""Robustness campaign (300 runs): per-run steady-state metric, outcome and drawn plant factors."""
import numpy as np
from matplotlib.ticker import NullFormatter

import data_g3
import style
from style import plt, INDIBLUE, INDIGREY, INDIORANGE, INDIGREEN, INDIRED

COL = {"pass": INDIGREEN, "fail": INDIRED, "loc": "black"}
LIM = 0.3  # steady-state horizontal RMS limit, m


def rate_bars(ax, rows, key, edges, xlabel, log=False):
    x = np.array([r[key] for r in rows])
    bad = np.array([r["status"] in ("fail", "loc") for r in rows])
    cen, frac, n = [], [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (x >= lo) & (x < hi)
        cen.append((lo, hi))
        n.append(m.sum())
        frac.append(100 * bad[m].mean() if m.any() else 0)
    for (lo, hi), f, k in zip(cen, frac, n):
        ax.bar((lo + hi) / 2 if not log else np.sqrt(lo * hi), f, width=(hi - lo) * 0.85 if not log else (hi - lo) * 0.7,
               color=INDIBLUE)
        ax.text((lo + hi) / 2 if not log else np.sqrt(lo * hi), f + 2, f"{k}", ha="center", fontsize=6.5, color=INDIGREY)
    if log:
        ax.set_xscale("log")
    ax.set_ylim(0, 100)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Runs failing (%)")


def main():
    rows = [r for r in data_g3.load() if r["status"] != "unscored"]
    fig, axs = plt.subplots(2, 2, figsize=(style.FULL, 4.2))
    a, b, c, d = axs.ravel()
    # (a) histogram of the steady-state metric
    scored = [r for r in rows if not np.isnan(r["rms"])]
    bins = np.linspace(0, 0.35, 36)
    data = [[r["rms"] for r in scored if r["status"] == s] for s in ("pass", "fail")]
    a.hist(data, bins=bins, stacked=True, color=[INDIGREEN, INDIRED], label=["pass", "fail"], lw=0)
    a.axvline(LIM, color=INDIORANGE, ls="--", lw=1.0)
    a.set_xlabel("Steady-state horizontal RMS (m)")
    a.set_ylabel("Runs")
    a.legend(loc="upper right", fontsize=7.5)
    # (b) metric against the motor time-constant factor
    for s in ("pass", "fail"):
        rr = [r for r in scored if r["status"] == s]
        b.plot([r["tau"] for r in rr], [r["rms"] for r in rr], "o", ms=2.6, mfc=COL[s], mec="none", alpha=0.75)
    b.axhline(LIM, color=INDIORANGE, ls="--", lw=1.0)
    b.set_xscale("log")
    b.set_xlim(0.45, 3.3)
    b.set_xticks([0.5, 1, 2, 3])
    b.set_xticklabels(["0.5", "1", "2", "3"])
    b.set_xlabel("Motor time constant (x nominal)")
    b.set_ylabel("Steady-state RMS (m)")
    loc = [r for r in rows if r["status"] == "loc"]
    b.plot([r["tau"] for r in loc], [0.36] * len(loc), "x", color="black", ms=6, mew=1.4, clip_on=False)
    b.text(3.2, 0.385, "loss of control", ha="right", fontsize=7, color="black")
    # (c), (d) failure fraction against drawn factors
    rate_bars(c, rows, "tau", [0.5, 0.8, 1.2, 1.8, 2.4, 3.01], "Motor time constant (x nominal)", log=True)
    c.set_xticks([0.5, 1, 2, 3])
    c.set_xticklabels(["0.5", "1", "2", "3"])
    rate_bars(d, rows, "delay", [0, 2, 4, 6, 8, 10.01], "Added loop delay (ms)")
    for ax in (b, c):
        ax.xaxis.set_minor_formatter(NullFormatter())
    for ax, l in zip((a, b, c, d), "abcd"):
        style.panel_label(ax, f"({l})")
    fig.tight_layout(h_pad=1.4, w_pad=1.2)
    style.save(fig, "g3_campaign")


if __name__ == "__main__":
    main()
