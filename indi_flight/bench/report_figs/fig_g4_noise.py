#!/usr/bin/env python3
"""Noise and effort: rotor-speed ripple and motor-command RMS per noise profile against their limits."""
import numpy as np

import data_g4
import style
from style import plt, INDIBLUE, INDIORANGE, INDIGREY

PROFILES = ("quiet", "typ", "harsh")
LABEL = {"quiet": "quiet", "typ": "typical", "harsh": "harsh"}
PANELS = [("r20", "Rotor-speed ripple,\n20 Hz band (%)"),
          ("c20", "Command RMS,\n20 Hz band (full scale)"),
          ("r4", "Rotor-speed ripple,\n4 Hz band (%)")]


def main():
    d = data_g4.load()
    fig, axs = plt.subplots(1, 3, figsize=(style.FULL, 2.6), sharey=True)
    rng = np.random.default_rng(2)
    rows = [(m, p) for m in ("hover", "cruise") for p in PROFILES]
    for ax, (key, xl) in zip(axs, PANELS):
        for i, (m, p) in enumerate(rows):
            runs = [v for k, v in d.items() if k.startswith(f"{m}_{p}_")]
            for v in runs:
                ax.plot(v[key], i + rng.uniform(-0.12, 0.12), "o", color=INDIBLUE, ms=3.5)
            lim = runs[0][key + "_lim"]
            ax.plot([lim, lim], [i - 0.35, i + 0.35], color=INDIORANGE, lw=1.6, solid_capstyle="butt")
        ax.set_xscale("log")
        ax.set_xlabel(xl)
        ax.set_ylim(len(rows) - 0.5, -0.5)
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([f"{m.capitalize()}, {LABEL[p]}" for m, p in rows])
        ax.grid(axis="y", visible=False)
        ax.axhline(2.5, color="#BBBBBB", lw=0.5)
    axs[0].set_xlim(1e-3, 8)
    axs[1].set_xlim(1e-5, 0.04)
    axs[2].set_xlim(3e-3, 15)
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="o", ls="", color=INDIBLUE, ms=3.5, label="INDI, one point per seed"),
         Line2D([], [], color=INDIORANGE, lw=1.6, label="limit")]
    fig.tight_layout(w_pad=0.8, rect=(0, 0, 1, 0.92))
    fig.legend(handles=h, loc="upper center", ncol=2, fontsize=7.5, handletextpad=0.4, columnspacing=1.5)
    style.save(fig, "g4_noise_effort")


if __name__ == "__main__":
    main()
