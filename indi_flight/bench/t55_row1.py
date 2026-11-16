"""T55 item 6: who publishes the trajectory_setpoint right after the first sp_hold row of a t53 hover run (Docker: pyulog).
usage: t55_row1.py <flight.ulg>"""
import sys

import numpy as np
from pyulog import ULog

u = ULog(sys.argv[1])
D = {}
for x in u.data_list:
    D.setdefault(x.name, x.data)
a, ts, s = D["sim_schedule_applied"], D["trajectory_setpoint"], D["vehicle_status"]
i = int(np.argmax(a["kind"] == 5))
t_row = int(a["timestamp"][i])
sp = [float(a["sp[%d]" % k][i]) for k in range(4)]
print("first sp_hold row at", t_row, "sp", sp)
t14 = int(next(t for t, n in zip(s["timestamp"], s["nav_state"]) if n == 14))
print("nav_state 14 first at", t14, "accepts_offboard_setpoints transitions:",
      [(int(t), int(v)) for j, (t, v) in enumerate(zip(s["timestamp"], s["accepts_offboard_setpoints"])) if j == 0 or v != s["accepts_offboard_setpoints"][j - 1]])
t = ts["timestamp"].astype(np.int64)
print("trajectory_setpoint samples", len(t), "median period us", int(np.median(np.diff(t))))
j0 = int(np.argmax(t > t_row))
for j in list(range(j0, j0 + 3)) + [int(np.argmax(t >= t14)) + k for k in range(0, 3)]:
    pos = [float(ts["position[%d]" % k][j]) for k in range(3)]
    print("  ts", int(t[j]), "pos", [round(p, 4) for p in pos], "yaw %.4f" % float(ts["yaw"][j]),
          "vel", [round(float(ts["velocity[%d]" % k][j]), 3) for k in range(3)], "d to sp (cm)", [round((pos[k] - sp[k]) * 100, 2) for k in range(3)])
m = (t > t_row) & (t < t14)
print("samples between the row and nav_state 14:", int(m.sum()), "distinct positions:", len({tuple(np.round([ts["position[%d]" % k][j] for k in range(3)], 5)) for j in np.where(m)[0]}))
for k in range(2):
    print("  between row and offboard: first / last sample pos", [round(float(ts["position[%d]" % q][np.where(m)[0][-k]]), 4) for q in range(3)] if m.any() else None)
