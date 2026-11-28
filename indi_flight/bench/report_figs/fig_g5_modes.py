#!/usr/bin/env python3
"""Modes and transitions: worst transient per row as a fraction of its limit."""
import data_g5
import style
from style import plt, INDIBLUE, INDIORANGE, INDIGREY


def main():
    rows = data_g5.ROWS
    fig, ax = plt.subplots(figsize=(style.FULL, 3.4))
    n = len(rows)
    for i, (lab, v, lim, unit, pid) in enumerate(rows):
        r = 100 * v / lim
        ax.plot([0, r], [i, i], color=INDIBLUE, lw=1.0)
        ax.plot(r, i, "o", color=INDIBLUE, ms=4.5)
        if pid is not None:
            ax.plot(100 * pid / lim, i, "D", mfc="white", mec=INDIGREY, mew=0.9, ms=4)
        ax.text(104, i, f"{v:g} / {lim:g} {unit}", va="center", fontsize=7, color=INDIGREY)
    ax.axvline(100, color=INDIORANGE, lw=1.1, ls="--")
    ax.set_ylim(n - 0.5, -0.5)
    ax.set_yticks(range(n))
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Worst case over three seeds (% of limit)")
    ax.grid(axis="y", visible=False)
    ax.spines["right"].set_visible(False)
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="o", ls="", color=INDIBLUE, ms=4.5, label="INDI"),
         Line2D([], [], marker="D", ls="", mfc="white", mec=INDIGREY, ms=4, label="PID reference"),
         Line2D([], [], color=INDIORANGE, ls="--", lw=1.1, label="limit")]
    ax.legend(handles=h, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=7.5)
    fig.subplots_adjust(right=0.8)
    style.save(fig, "g5_modes")


if __name__ == "__main__":
    main()
