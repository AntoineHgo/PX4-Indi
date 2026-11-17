#!/usr/bin/env python3
"""INDI vs PID inner-loop comparison plots from the paired flights in this folder.

  python3 plot_compare.py DIR          (DIR = this folder; writes DIR/plots/*.png and DIR/metrics.md)

Per step scenario: attitude (estimate vs setpoint) and body rate (estimate vs setpoint) on the stepped axis,
INDI and PID overlaid, time from the scenario window start. Torque-step disturbance: roll/pitch/yaw attitude and
rate deviation from the pre-disturbance mean, applied torque shaded.
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from pyulog import ULog  # noqa: E402

D = sys.argv[1]
OUT = os.path.join(D, "plots")
os.makedirs(OUT, exist_ok=True)
C = {"indi": "#2a78d6", "pid": "#eb6834"}
LBL = {"indi": "INDI", "pid": "PID"}
SP = "#8a8985"
AX = {"roll": 0, "pitch": 1, "yaw": 2}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#e4e3df", "grid.linewidth": 0.6, "lines.linewidth": 1.6,
                     "axes.edgecolor": "#8a8985", "axes.labelcolor": "#52514e", "xtick.color": "#52514e",
                     "ytick.color": "#52514e", "legend.frameon": False})


def q2e(q):
    w, x, y, z = q.T
    r = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    p = np.arcsin(np.clip(2 * (w * y - z * x), -1, 1))
    yw = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return np.degrees(np.vstack([r, p, yw]).T)


def load(run):
    d = os.path.join(D, run)
    u = ULog(os.path.join(d, "flight.ulg"))
    meta = json.load(open(os.path.join(d, "run.json")))

    def topic(name):
        return next(x for x in u.data_list if x.name == name and x.multi_id == 0).data

    att, asp = topic("vehicle_attitude"), topic("vehicle_attitude_setpoint")
    av, rsp = topic("vehicle_angular_velocity"), topic("vehicle_rates_setpoint")
    t0 = meta["t_window_start_us"]

    def rel(ts):  # ULog timestamps are uint64: subtract as signed or samples before t0 wrap to ~1.8e13 s
        return (ts.astype(np.int64) - t0) * 1e-6

    r = {"meta": meta, "t0": t0}
    r["att_t"] = rel(att["timestamp"])
    r["att"] = q2e(np.vstack([att[f"q[{i}]"] for i in range(4)]).T)
    r["asp_t"] = rel(asp["timestamp"])
    r["asp"] = q2e(np.vstack([asp[f"q_d[{i}]"] for i in range(4)]).T)
    r["av_t"] = rel(av["timestamp"])
    r["av"] = np.degrees(np.vstack([av[f"xyz[{i}]"] for i in range(3)]).T)
    r["rsp_t"] = rel(rsp["timestamp"])
    r["rsp"] = np.degrees(np.vstack([rsp["roll"], rsp["pitch"], rsp["yaw"]]).T)
    if meta.get("disturbance"):
        dc = np.genfromtxt(os.path.join(d, "disturbance.csv"), delimiter=",", names=True)
        r["dist_t"] = dc["px4_time_s"] - t0 * 1e-6
        r["dist"] = np.vstack([dc["tx"], dc["ty"], dc["tz"]]).T
    return r


def unwrap_deg(a):
    return np.degrees(np.unwrap(np.radians(a)))


def step_metrics(t, y, ts, ysp, t_on, t_off, amp):
    """Rise 10-90 %, overshoot, 2 % settling (of amp) for a step from 0 to amp at t_on."""
    m = (t >= t_on) & (t < t_off)
    tt, yy = t[m] - t_on, y[m] * np.sign(amp)
    a = abs(amp)
    i10 = np.argmax(yy >= 0.1 * a)
    i90 = np.argmax(yy >= 0.9 * a)
    rise = tt[i90] - tt[i10] if yy.max() >= 0.9 * a else np.nan
    os_ = max(0.0, (yy.max() - a) / a * 100)
    out = np.abs(yy - a) > 0.02 * a
    settle = tt[np.nonzero(out)[0][-1] + 1] if out.any() and np.nonzero(out)[0][-1] + 1 < len(tt) else np.nan
    return rise * 1e3, os_, settle * 1e3


lines = ["# INDI vs PID, quad5in, sim v2, 800 Hz, seed 1\n",
         "| scenario | step | controller | rise 10-90 % [ms] | overshoot [%] | settle 2 % [ms] | rate track RMS [deg/s] |",
         "|---|---|---|---|---|---|---|"]

for scen, axis, amp in (("step_roll", "roll", 15), ("step_pitch", "pitch", 15), ("step_yaw", "yaw", 45)):
    runs = {c: load(f"{scen}_{c}") for c in ("indi", "pid") if os.path.exists(os.path.join(D, f"{scen}_{c}", "run.json"))}
    if not runs:
        continue
    k = AX[axis]
    fig, axs = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True)
    segs = next(iter(runs.values()))["meta"].get("segments") or []
    for c, r in runs.items():
        a = unwrap_deg(r["att"][:, k]) if axis == "yaw" else r["att"][:, k]
        s = unwrap_deg(r["asp"][:, k]) if axis == "yaw" else r["asp"][:, k]
        if axis == "yaw":  # relative to the pre-step heading
            ref = np.median(s[(r["asp_t"] > 0) & (r["asp_t"] < 1.5)])
            a, s = a - ref, s - ref
        axs[0].plot(r["att_t"], a, color=C[c], label=f"{LBL[c]} estimate")
        axs[0].plot(r["asp_t"], s, color=C[c], ls="--", lw=1.0, alpha=0.8, label=f"{LBL[c]} setpoint")
        axs[1].plot(r["av_t"], r["av"][:, k], color=C[c], label=f"{LBL[c]} estimate")
        axs[1].plot(r["rsp_t"], r["rsp"][:, k], color=C[c], ls="--", lw=1.0, alpha=0.8, label=f"{LBL[c]} setpoint")
        # metrics on the first up-step (setpoint goes 0 -> amp at 2.0 s)
        rise, os_, settle = step_metrics(r["att_t"], a, r["asp_t"], s, 2.0, 5.0, amp)
        sp_i = np.interp(r["av_t"], r["rsp_t"], r["rsp"][:, k])
        w = (r["av_t"] > 0) & (r["av_t"] < r["av_t"].max())
        w &= r["av_t"] < (r["att_t"][-1] if False else 1e9)
        win = (r["av_t"] > 0) & (r["av_t"] < 14)
        rms = np.sqrt(np.mean((r["av"][win, k] - sp_i[win]) ** 2))
        lines.append(f"| {scen} | {amp} deg | {LBL[c]} | {rise:.0f} | {os_:.1f} | {settle:.0f} | {rms:.1f} |")
    axs[0].set_ylabel(f"{axis} angle [deg]")
    axs[1].set_ylabel(f"{axis} rate [deg/s]")
    axs[1].set_xlabel("time from scenario start [s]")
    axs[0].set_title(f"{axis.capitalize()} steps ±{amp}°: attitude and body rate, estimate (solid) vs setpoint (dashed)",
                     loc="left", fontsize=11)
    axs[0].legend(ncol=4, loc="upper right", fontsize=9)
    axs[1].set_xlim(0, 14)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f"{scen}.png"), dpi=130)
    # zoom on the first up-step
    for ax in axs:
        ax.set_xlim(1.9, 3.0)
    axs[0].set_ylim(-0.15 * amp, 1.3 * amp)
    axs[1].set_ylim(-0.4 * axs[1].get_ylim()[1], None)
    axs[0].legend(ncol=4, loc="lower right", fontsize=9)
    axs[0].set_title(f"{axis.capitalize()} +{amp}° step, zoom", loc="left", fontsize=11)
    fig.savefig(os.path.join(OUT, f"{scen}_zoom.png"), dpi=130)
    plt.close(fig)

# ---- torque-step disturbance rejection ----
runs = {c: load(f"torque_steps_{c}") for c in ("indi", "pid") if os.path.exists(os.path.join(D, f"torque_steps_{c}", "run.json"))}
if runs:
    fig, axs = plt.subplots(3, 3, figsize=(14, 8.5), sharex=True)
    lines += ["", "| torque step | controller | peak angle dev [deg] | peak rate dev [deg/s] | angle dev RMS during step [deg] |",
              "|---|---|---|---|---|"]
    for c, r in runs.items():
        onset = r["meta"]["disturbance"]["onset_us"] * 1e-6 - r["t0"] * 1e-6
        ta, tv = r["att_t"] - onset, r["av_t"] - onset
        td = r["dist_t"] - onset
        for k, name in enumerate(("roll", "pitch", "yaw")):
            a = unwrap_deg(r["att"][:, k])
            pre = (ta > -2) & (ta < 0)
            dev = a - np.mean(a[pre])
            axs[0, k].plot(ta, dev, color=C[c], label=LBL[c])
            axs[1, k].plot(tv, r["av"][:, k], color=C[c], label=LBL[c])
            if c == "indi":
                axs[2, k].fill_between(td, r["dist"][:, k] * 1e3, color=SP, alpha=0.35, lw=0, step="post")
                axs[2, k].plot(td, r["dist"][:, k] * 1e3, color=SP, lw=1.0, drawstyle="steps-post")
            t_on = 4.0 * k
            m = (ta >= t_on) & (ta < t_on + 2.5)
            mv = (tv >= t_on) & (tv < t_on + 2.5)
            lines.append(f"| {name} | {LBL[c]} | {np.abs(dev[m]).max():.2f} | {np.abs(r['av'][mv, k]).max():.1f} | "
                         f"{np.sqrt(np.mean(dev[(ta >= t_on) & (ta < t_on + 2)] ** 2)):.2f} |")
        for k, name in enumerate(("roll", "pitch", "yaw")):
            axs[0, k].set_title(f"{name}  ({[100, 100, 30][k]} mN·m step, {4 * k}-{4 * k + 2} s)", loc="left", fontsize=10)
    axs[0, 0].set_ylabel("angle deviation [deg]")
    axs[1, 0].set_ylabel("body rate [deg/s]")
    axs[2, 0].set_ylabel("applied torque [mN·m]")
    for ax in axs[2]:
        ax.set_xlabel("time from disturbance onset [s]")
    axs[0, 0].legend(loc="lower left")
    axs[0, 0].set_xlim(-1, 12)
    fig.suptitle("Torque-step disturbance rejection in position hold (same attitude/position loops, rate loop INDI vs PID)",
                 x=0.01, ha="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "torque_steps.png"), dpi=130)
    plt.close(fig)

open(os.path.join(D, "metrics.md"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
