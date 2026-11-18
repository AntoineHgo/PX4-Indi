import sys, numpy as np
sys.path.insert(0, "/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/delay_pretest_s102")
from check_delay import ds, hp, ULog, GRID_US, TRIM
for p in sys.argv[1:]:
    u = ULog(p, message_name_filter_list=["actuator_motors", "esc_status", "vehicle_land_detected"])
    am, esc, ld = ds(u, "actuator_motors"), ds(u, "esc_status"), ds(u, "vehicle_land_detected")
    t0 = ld["timestamp"][ld["landed"] == 0][0] + 4e6; g = np.arange(t0, t0 + 15e6, GRID_US)
    r_ = esc["esc[0].esc_rpm"].astype(float); ch = np.count_nonzero(np.diff(r_)) / (esc["timestamp"][-1] - esc["timestamp"][0]) * 1e6
    c = hp(np.interp(g, am["timestamp"].astype(float), am["control[0]"].astype(float)))[TRIM:-TRIM]
    r = hp(np.interp(g, esc["timestamp"].astype(float), r_))[TRIM:-TRIM]
    cc = {L: np.dot(c[:len(c)-L], r[L:]) / (len(c)-L) if L >= 0 else np.dot(c[-L:], r[:len(r)+L]) / (len(c)+L) for L in range(-8, 33)}
    best = max(cc, key=cc.get)
    print(p.split('/')[-2], f"esc_rpm value-changes/s {ch:.0f}", f"ctrl std {c.std():.4f} rpm-hp std {r.std():.1f}",
          f"peak lag {best*1.25:.2f} ms", " ".join(f"{L*1.25:.2f}:{cc[L]/max(cc.values()):.2f}" for L in (0, 4, 8, 16, 24, 28, 32)))
