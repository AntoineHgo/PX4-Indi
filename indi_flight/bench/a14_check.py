#!/usr/bin/env python3
"""A-14 check: EKF vs ground-truth altitude around arming.

For each ULog given on the command line this reports, over the interval from
the first vehicle_status sample with arming_state == 2 (armed) to arm + 20 s:

  * max |z_ekf - z_true| and its time relative to arm,
  * z_ekf and z_true at arm,
  * vehicle_local_position z_reset_counter changes and delta_z events,
  * vehicle_air_data baro_alt_meter change vs truth altitude change,
  * the EKF-minus-truth residual over arm + 55 s .. arm + 85 s.

Truth (vehicle_local_position_groundtruth, ~800 Hz) is linearly interpolated
onto the EKF (vehicle_local_position, ~89 Hz) timestamps. All z values are
NED down (metres), as stored in the ULog. Baro-derived altitude is
-(baro_alt_meter - baro_alt_meter at arm), i.e. NED down.

Writes a markdown table to --out and one PNG per log next to it.

Usage:
  python3 indi_flight/bench/a14_check.py LOG1.ulg LOG2.ulg \
      --labels r1,r2 --out indi_flight/results/a14_s20/table.md
"""

import argparse
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from pyulog import ULog  # noqa: E402

ARMED = 2
WINDOW_S = 20.0
EARLY_S = 8.0
HOVER_S = (55.0, 85.0)
PLOT_PRE_S = 5.0


def topic(ulog, name):
    return ulog.get_dataset(name).data


def analyse(path):
    ulog = ULog(path)
    st = topic(ulog, "vehicle_status")
    armed_idx = np.nonzero(st["arming_state"] == ARMED)[0]
    if armed_idx.size == 0:
        raise SystemExit(f"{path}: no vehicle_status sample with arming_state == 2")
    t_arm = st["timestamp"][armed_idx[0]] * 1e-6

    lp = topic(ulog, "vehicle_local_position")
    gt = topic(ulog, "vehicle_local_position_groundtruth")
    ad = topic(ulog, "vehicle_air_data")

    te = lp["timestamp"] * 1e-6
    ze = lp["z"].astype(float)
    tt = gt["timestamp"] * 1e-6
    zt = gt["z"].astype(float)
    tb = ad["timestamp"] * 1e-6
    baro = ad["baro_alt_meter"].astype(float)

    def z_true_at(t):
        return np.interp(t, tt, zt)

    def z_ekf_at(t):
        return np.interp(t, te, ze)

    def baro_at(t):
        return np.interp(t, tb, baro)

    m = (te >= t_arm) & (te <= t_arm + WINDOW_S)
    res = ze[m] - z_true_at(te[m])
    rel = te[m] - t_arm
    i_max = int(np.argmax(np.abs(res)))

    early = (te >= t_arm) & (te <= t_arm + EARLY_S)
    res_early = ze[early] - z_true_at(te[early])

    mh = (te >= t_arm + HOVER_S[0]) & (te <= t_arm + HOVER_S[1])
    res_h = ze[mh] - z_true_at(te[mh])

    rc = lp["z_reset_counter"]
    rc_changes = np.nonzero(np.diff(rc))[0] + 1
    rc_events = [
        f"t={te[k] - t_arm:+.2f}s ({int(rc[k - 1])}->{int(rc[k])})" for k in rc_changes
    ]

    # delta_z is a persistent field (non-zero for the whole log when set once),
    # so report value changes, not non-zero samples.
    dz = lp["delta_z"].astype(float)
    dz_chg = [k for k in (np.nonzero(np.diff(dz) != 0.0)[0] + 1) if m[k]]
    dz_arm = float(dz[np.searchsorted(te, t_arm)])
    dz_txt = (
        f"value at arm {dz_arm:.3f} m; {len(dz_chg)} value changes in window"
        + ("".join(f"; t={te[k] - t_arm:+.2f}s {dz[k - 1]:.3f}->{dz[k]:.3f}" for k in dz_chg[:5]) if dz_chg else "")
        + f"; log range [{dz.min():.3f}, {dz.max():.3f}] m"
    )

    baro_arm = baro_at(t_arm)
    baro_end = baro_at(t_arm + WINDOW_S)
    baro_change = baro_end - baro_arm  # up-positive
    truth_alt_change = -(z_true_at(t_arm + WINDOW_S) - z_true_at(t_arm))
    ekf_alt_change = -(z_ekf_at(t_arm + WINDOW_S) - z_ekf_at(t_arm))

    # Plot: arm-5 s .. arm+20 s, z_ekf, z_true, baro-derived NED-down z.
    p0, p1 = t_arm - PLOT_PRE_S, t_arm + WINDOW_S
    pm = (te >= p0) & (te <= p1)
    pt = (tt >= p0) & (tt <= p1)
    pb = (tb >= p0) & (tb <= p1)
    z_baro_ned = -(baro - baro_arm)

    return {
        "path": path,
        "t_arm": t_arm,
        "max_abs_res": float(np.max(np.abs(res))),
        "t_max": float(rel[i_max]),
        "res_at_max": float(res[i_max]),
        "max_abs_res_0_8s": float(np.max(np.abs(res_early))),
        "z_ekf_arm": float(z_ekf_at(t_arm)),
        "z_true_arm": float(z_true_at(t_arm)),
        "rc_at_arm": int(rc[np.searchsorted(te, t_arm)]) if te[0] <= t_arm else int(rc[0]),
        "rc_events": rc_events if rc_events else ["none"],
        "dz": dz_txt,
        "baro_change": float(baro_change),
        "truth_alt_change": float(truth_alt_change),
        "ekf_alt_change": float(ekf_alt_change),
        "baro_minus_truth": float(baro_change - truth_alt_change),
        "hover_max_abs": float(np.max(np.abs(res_h))) if res_h.size else float("nan"),
        "hover_mean": float(np.mean(res_h)) if res_h.size else float("nan"),
        "hover_rms": float(np.sqrt(np.mean(res_h**2))) if res_h.size else float("nan"),
        "_plot": (
            te[pm] - t_arm,
            ze[pm],
            tt[pt] - t_arm,
            zt[pt],
            tb[pb] - t_arm,
            z_baro_ned[pb],
        ),
    }


def plot(res, label, out_png):
    tEk, zEk, tTr, zTr, tBa, zBa = res["_plot"]
    fig, (ax0, ax1) = plt.subplots(2, 1, sharex=True, figsize=(9, 6), gridspec_kw={"height_ratios": [3, 1]})
    ax0.plot(tEk, zEk, lw=1.2, label="z_ekf (vehicle_local_position)")
    ax0.plot(tTr, zTr, lw=1.2, label="z_true (groundtruth)")
    ax0.plot(tBa, zBa, ".", ms=3, label="baro-derived z (NED down)")
    ax0.axvline(0.0, color="k", ls=":", lw=0.8, label="arm")
    ax0.set_ylabel("z, NED down [m]")
    ax0.set_title(f"A-14 {label}: arm-5 s .. arm+20 s")
    ax0.legend(loc="best", fontsize=8)
    ax0.grid(alpha=0.3)
    # residual on the EKF grid
    zt_on_ekf = np.interp(tEk + res["t_arm"], tTr + res["t_arm"], zTr)
    ax1.plot(tEk, zEk - zt_on_ekf, lw=1.0, color="C3")
    ax1.axhline(0.0, color="k", lw=0.6)
    ax1.axvline(0.0, color="k", ls=":", lw=0.8)
    ax1.set_ylabel("z_ekf - z_true [m]")
    ax1.set_xlabel("t - t_arm [s]")
    ax1.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_png, dpi=120)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ulogs", nargs="+", help="ULog files")
    ap.add_argument("--labels", default=None, help="comma-separated labels, one per ULog")
    ap.add_argument("--out", required=True, help="markdown output path")
    args = ap.parse_args()

    labels = args.labels.split(",") if args.labels else [os.path.basename(os.path.dirname(os.path.abspath(p))) for p in args.ulogs]
    if len(labels) != len(args.ulogs):
        raise SystemExit("--labels count must match the number of ULogs")

    outdir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(outdir, exist_ok=True)

    results = []
    for path, label in zip(args.ulogs, labels):
        r = analyse(path)
        r["label"] = label
        plot(r, label, os.path.join(outdir, f"a14_{label}_arm_window.png"))
        results.append(r)

    def fmt(x):
        return f"{x:+.3f}" if isinstance(x, float) else str(x)

    rows = [
        ("source ULog", lambda r: f"`{r['path']}`"),
        ("arm time (log s)", lambda r: f"{r['t_arm']:.2f}"),
        ("max abs(z_ekf - z_true), arm..arm+20 s [m]", lambda r: f"{r['max_abs_res']:.3f}"),
        ("time of that max, rel. arm [s]", lambda r: f"{r['t_max']:+.2f}"),
        ("signed residual at that max [m]", lambda r: f"{r['res_at_max']:+.3f}"),
        ("max abs residual, arm..arm+8 s [m]", lambda r: f"{r['max_abs_res_0_8s']:.3f}"),
        ("z_ekf at arm [m, NED down]", lambda r: f"{r['z_ekf_arm']:+.3f}"),
        ("z_true at arm [m, NED down]", lambda r: f"{r['z_true_arm']:+.3f}"),
        ("z_reset_counter at arm", lambda r: str(r["rc_at_arm"])),
        ("z_reset_counter changes in log (rel. arm)", lambda r: "; ".join(r["rc_events"])),
        ("delta_z events, arm..arm+20 s", lambda r: r["dz"]),
        ("baro_alt_meter change, arm..arm+20 s [m, up]", lambda r: f"{r['baro_change']:+.3f}"),
        ("truth altitude change, arm..arm+20 s [m, up]", lambda r: f"{r['truth_alt_change']:+.3f}"),
        ("EKF altitude change, arm..arm+20 s [m, up]", lambda r: f"{r['ekf_alt_change']:+.3f}"),
        ("baro change minus truth change [m]", lambda r: f"{r['baro_minus_truth']:+.3f}"),
        ("residual arm+55..arm+85 s: max abs [m]", lambda r: f"{r['hover_max_abs']:.3f}"),
        ("residual arm+55..arm+85 s: mean [m]", lambda r: f"{r['hover_mean']:+.3f}"),
        ("residual arm+55..arm+85 s: rms [m]", lambda r: f"{r['hover_rms']:.3f}"),
    ]
    lines = ["| metric | " + " | ".join(r["label"] for r in results) + " |",
             "|---" * (len(results) + 1) + "|"]
    for name, f in rows:
        lines.append(f"| {name} | " + " | ".join(f(r) for r in results) + " |")
    table = "\n".join(lines) + "\n"
    with open(args.out, "w") as fh:
        fh.write(table)
    print(table)


if __name__ == "__main__":
    main()
