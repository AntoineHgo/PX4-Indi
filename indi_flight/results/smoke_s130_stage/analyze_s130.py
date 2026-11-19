import sys, math, json
import numpy as np
from pyulog import ULog

def get(ul, name):
    for d in ul.data_list:
        if d.name == name:
            return d.data
    return None

def tilt_deg(q):
    w, x, y, z = q
    c = 1 - 2 * (x * x + y * y)
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))

out = {}
for run in ["hover", "posctl"]:
    path = f"indi_flight/results/smoke_s130_stage/{run}/flight.ulg"
    ul = ULog(path)
    t0 = ul.start_timestamp
    t = lambda a: (a - t0) * 1e-6
    r = {}
    ind = get(ul, "indi_pos_status")
    ls = get(ul, "vehicle_land_detected")
    vs = get(ul, "vehicle_status")
    if ind is not None:
        ts = t(ind["timestamp"]); sm = ind["stage_mode"].astype(int)
        # airborne from land detector
        if ls is not None:
            lt = t(ls["timestamp"]); landed = ls["landed"].astype(bool)
            idx = np.searchsorted(lt, ts, side="right") - 1
            air = np.where(idx >= 0, ~landed[np.clip(idx, 0, None)], False)
        else:
            air = np.ones_like(sm, dtype=bool)
        r["stage_mode_all"] = {int(k): int(v) for k, v in zip(*np.unique(sm, return_counts=True))}
        r["stage_mode_airborne"] = {int(k): int(v) for k, v in zip(*np.unique(sm[air], return_counts=True))}
        r["stage_mode_ground"] = {int(k): int(v) for k, v in zip(*np.unique(sm[~air], return_counts=True))}
        ch = np.nonzero(np.diff(sm))[0]
        r["stage_mode_changes_t"] = [(round(float(ts[i+1]), 2), int(sm[i]), int(sm[i+1])) for i in ch][:30]
        r["stage_mode_first_airborne_t"] = round(float(ts[np.argmax(air)]), 2) if air.any() else None
    if vs is not None:
        nt = t(vs["timestamp"]); nav = vs["nav_state"].astype(int)
        ch = np.nonzero(np.diff(nav))[0]
        r["nav_changes"] = [(round(float(nt[i+1]), 2), int(nav[i]), int(nav[i+1])) for i in ch]
    if ls is not None:
        lt = t(ls["timestamp"]); landed = ls["landed"].astype(bool)
        ch = np.nonzero(np.diff(landed.astype(int)))[0]
        r["landed_changes"] = [(round(float(lt[i+1]), 2), bool(landed[i+1])) for i in ch]
    lp = get(ul, "vehicle_local_position_groundtruth")
    if lp is None:
        lp = get(ul, "vehicle_local_position")
    av = get(ul, "vehicle_angular_velocity")
    att = get(ul, "vehicle_attitude")
    win = (55.025, 85.025) if run == "hover" else (55.0, 63.1)
    lt = t(lp["timestamp"]); m = (lt >= win[0]) & (lt <= win[1])
    z = lp["z"][m]; x = lp["x"][m]; y = lp["y"][m]
    r["window"] = win
    r["z_mean"] = round(float(z.mean()), 3); r["z_std"] = round(float(z.std()), 4)
    r["max_dx"] = round(float(np.max(np.abs(x - x.mean()))), 3)
    r["max_dy"] = round(float(np.max(np.abs(y - y.mean()))), 3)
    at = t(av["timestamp"]); am = (at >= win[0]) & (at <= win[1])
    wn = np.sqrt(av["xyz[0]"]**2 + av["xyz[1]"]**2 + av["xyz[2]"]**2)[am]
    r["max_rate"] = round(float(wn.max()), 4)
    if att is not None:
        ct = t(att["timestamp"]); cm = (ct >= win[0]) & (ct <= win[1])
        q = np.stack([att["q[0]"], att["q[1]"], att["q[2]"], att["q[3]"]], axis=1)[cm]
        r["max_tilt_deg"] = round(max(tilt_deg(qq) for qq in q[::5]), 3)
    if run == "posctl":
        means = []
        for s in range(36, 57):
            mm = (lt >= s) & (lt < s + 1)
            if mm.any():
                means.append(f"{s}:{lp['z'][mm].mean():.2f}")
        r["z_1s_means"] = means
        m2 = (lt >= 45) & (lt <= 58)
        r["z_std_45_58"] = round(float(lp["z"][m2].std()), 3)
    out[run] = r
print(json.dumps(out, indent=1, default=str))
