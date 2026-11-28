#!/usr/bin/env python3
"""Attitude step responses (roll, pitch, yaw): INDI at the frozen configuration against the PID reference."""
import numpy as np

import data_steps as ds
import style
from style import plt, INDIBLUE, INDIGREY, INDIORANGE, INDILIGHT


def main():
    fig, axs = plt.subplots(2, 3, figsize=(style.FULL, 3.3), sharex="col")
    for j, ax_name in enumerate(ds.AXES):
        i_, p_ = ds.load("indi", ax_name), ds.load("pid", ax_name)
        a, b = axs[0, j], axs[1, j]
        sp = i_["att_sp_deg"]
        amp = sp[-1]
        a.axhspan(amp * 0.98, amp * 1.02, color=INDILIGHT, lw=0)
        a.plot(i_["t_s"], sp, color="black", lw=0.7, ls="--", label="setpoint")
        a.plot(p_["t_s"], p_["att_deg"], color=INDIGREY, label="PID reference")
        a.plot(i_["t_s"], i_["att_deg"], color=INDIBLUE, label="INDI")
        b.plot(p_["t_s"], p_["rate_dps"], color=INDIGREY)
        b.plot(i_["t_s"], i_["rate_dps"], color=INDIBLUE)
        a.set_title(ax_name.capitalize(), fontsize=9)
        b.set_xlabel("Time after step (s)")
        a.set_xlim(-0.2, 1.5 if ax_name != "yaw" else 3.0)
        if j == 0:
            a.set_ylabel("Angle (deg)")
            b.set_ylabel("Rate (deg/s)")
    axs[0, 0].legend(loc="lower right", fontsize=7, handlelength=1.4)
    fig.tight_layout(h_pad=0.4, w_pad=0.6)
    style.save(fig, "step_attitude")


if __name__ == "__main__":
    main()
