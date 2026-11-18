"""Independent key for S98 stage5 flights. Raw ULG only; fault times from run.json motor_fault.event_us."""
import json, sys
import numpy as np
from pyulog import ULog

ROOT = "/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/stage5_s98"
FLIGHTS = {
    "A_gap085": f"{ROOT}/A_gap085/run",
    "B_altctl": f"{ROOT}/B_altctl/run",
    "C_altctl_at": f"{ROOT}/C_altctl_at/run",
}

def topic(ulog, name):
    for d in ulog.data_list:
        if d.name == name:
            return d.data
    return None

def window(t, lo, hi):
    return (t >= lo) & (t <= hi)

rows = []
for name, run in FLIGHTS.items():
    meta = json.load(open(f"{run}/run.json"))
    fault_us = meta["motor_fault"]["event_us"]
    scale = meta["motor_fault"]["thrust_scale"]
    ul = ULog(f"{run}/flight.ulg")
    gt = topic(ul, "vehicle_local_position_groundtruth")
    src = "groundtruth"
    if gt is None:
        gt = topic(ul, "vehicle_local_position"); src = "vehicle_local_position (NOT ground truth)"
    ts = gt["timestamp"].astype(float) * 1e-6
    z = gt["z"].astype(float)
    ok = np.isfinite(z)
    ts, z = ts[ok], z[ok]
    t_f = fault_us * 1e-6
    ref = z[window(ts, t_f - 5, t_f)].mean()
    post = window(ts, t_f, ts.max())
    peak = np.max(np.abs(z[post] - ref))
    peak20 = np.max(np.abs(z[window(ts, t_f, t_f + 20)] - ref))
    m1020 = (z[window(ts, t_f + 10, t_f + 20)] - ref).mean()
    # landing / disarm
    st = topic(ul, "vehicle_status")
    arm_t = st["timestamp"].astype(float) * 1e-6
    disarm = arm_t[(st["arming_state"] == 1) & (arm_t > t_f)]
    t_disarm = disarm[0] if len(disarm) else ts.max()
    ld = topic(ul, "vehicle_land_detected")
    ld_t = ld["timestamp"].astype(float) * 1e-6
    landed = ld_t[(ld["landed"] == 1) & (ld_t > t_f)]
    t_land = landed[0] if len(landed) else t_disarm
    t_end = min(t_land, t_disarm)
    last10 = (z[window(ts, t_end - 10, t_end)] - ref).mean()
    # body rate magnitude
    av = topic(ul, "vehicle_angular_velocity")
    av_t = av["timestamp"].astype(float) * 1e-6
    w = np.sqrt(av["xyz[0]"]**2 + av["xyz[1]"]**2 + av["xyz[2]"]**2)
    wsel = w[window(av_t, t_f + 10, t_f + 20)]
    rms = np.sqrt(np.mean(wsel**2))
    rows.append((name, scale, t_f, src, ref, peak, peak20, m1020, last10, t_end, rms,
                 ts.min(), ts.max(), av_t.min(), av_t.max()))


out = []
out.append("| flight | scale | fault_t [s] | src | ref z [m] | peak abs(z-ref) to fault+20 [m] | peak abs(z-ref) to end [m] | mean(z-ref) t+10..20 [m] | mean(z-ref) last10 before land [m] | t_end [s] | RMS body rate [rad/s] |")
out.append("|---|---|---|---|---|---|---|---|---|---|---|")
for r in rows:
    out.append(f"| {r[0]} | {r[1]} | {r[2]:.3f} | {r[3]} | {r[4]:.3f} | {r[5]:.3f} | {r[6]:.3f} | {r[7]:+.3f} | {r[8]:+.3f} | {r[9]:.2f} | {r[10]:.4f} |")
out.append("")
out.append("log time ranges (s): " + "; ".join(f"{r[0]} gt[{r[11]:.2f},{r[12]:.2f}] angvel[{r[13]:.2f},{r[14]:.2f}]" for r in rows))
print("\n".join(out))
