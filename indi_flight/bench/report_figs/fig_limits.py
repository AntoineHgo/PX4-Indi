#!/usr/bin/env python3
"""The two robustness failures that are specific to INDI: sustained 2 Hz pitch oscillation (slow motors) and
loss of control on thrust saturation with a weak motor, each against the PID reference on the same draw."""
import numpy as np

import style
from style import path, plt, INDIBLUE, INDIGREY, INDIORANGE


def csv(name):
    d = np.genfromtxt(path(f"results/report_traces/{name}.csv"), delimiter=",", names=True)
    return {k: d[k] for k in d.dtype.names}


def main():
    s3, s264 = csv("g3_draw3_pitch_rate"), csv("g3_draw264_tilt")
    fig = plt.figure(figsize=(style.FULL, 3.9))
    gs = fig.add_gridspec(2, 2, hspace=0.55, wspace=0.32)
    a = fig.add_subplot(gs[0, :])
    b = fig.add_subplot(gs[1, 0])
    c = fig.add_subplot(gs[1, 1], sharex=b)
    a.plot(s3["t_s"], s3["q_pid_dps"], color=INDIGREY, lw=0.9, label="PID reference")
    a.plot(s3["t_s"], s3["q_indi_dps"], color=INDIBLUE, lw=0.9, label="INDI")
    a.set_xlabel("Time (s)")
    a.set_ylabel("Pitch rate (deg/s)")
    a.set_xlim(0, 8)
    a.legend(loc="upper right", ncol=2, fontsize=7.5)
    b.plot(s264["t_s"], s264["tilt_pid_deg"], color=INDIGREY, label="PID reference")
    b.plot(s264["t_s"], s264["tilt_indi_deg"], color=INDIBLUE, label="INDI")
    b.axhline(60, color=INDIORANGE, ls="--", lw=1.0)
    b.text(3.15, 62, "60 deg", color=INDIORANGE, fontsize=7.5, va="bottom", ha="right")
    b.set_ylim(0, 90)
    b.set_ylabel("Tilt (deg)")
    b.set_xlabel("Time after the fault (s)")
    c.plot(s264["t_s"], s264["q_pid_dps"], color=INDIGREY)
    c.plot(s264["t_s"], s264["q_indi_dps"], color=INDIBLUE)
    c.set_ylabel("Pitch rate (deg/s)")
    c.set_xlabel("Time after the fault (s)")
    b.set_xlim(-1.0, 3.2)
    for ax, l in zip((a, b, c), "abc"):
        style.panel_label(ax, f"({l})")
    style.save(fig, "limits_failures")


if __name__ == "__main__":
    main()
