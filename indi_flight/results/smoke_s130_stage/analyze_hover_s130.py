import math
import numpy as np
from pyulog import ULog
ul = ULog("indi_flight/results/smoke_s130_stage/hover/flight.ulg")
t0 = ul.start_timestamp
D = {d.name: d.data for d in ul.data_list}
t = lambda a: (a - t0) * 1e-6
lp = D["vehicle_local_position_groundtruth"]; lt = t(lp["timestamp"])
av = D["vehicle_angular_velocity"]; at = t(av["timestamp"])
ind = D["indi_pos_status"]; it = t(ind["timestamp"])
print("indi_pos_status first/last t:", round(float(it[0]), 2), round(float(it[-1]), 2))
vc = D.get("vehicle_command")
if vc is not None:
    ct = t(vc["timestamp"])
    for i in range(len(ct)):
        if int(vc["command"][i]) in (21, 176, 400, 22):
            print("cmd", int(vc["command"][i]), round(float(ct[i]), 2))
print("z 1s means (NED):", [f"{s}:{lp['z'][(lt>=s)&(lt<s+1)].mean():.2f}" for s in range(30, 82, 2) if ((lt>=s)&(lt<s+1)).any()])
for w in [(55.025, 69.5), (60.0, 69.0)]:
    m = (lt >= w[0]) & (lt <= w[1])
    x, y, z = lp["x"][m], lp["y"][m], lp["z"][m]
    am = (at >= w[0]) & (at <= w[1])
    rate = np.sqrt(av["xyz[0]"]**2 + av["xyz[1]"]**2 + av["xyz[2]"]**2)[am]
    print(f"window {w}: n={m.sum()} z_mean={z.mean():.3f} z_std={z.std():.4f} max_dx={np.max(np.abs(x-x.mean())):.3f} max_dy={np.max(np.abs(y-y.mean())):.3f} max_rate={rate.max():.4f}")
