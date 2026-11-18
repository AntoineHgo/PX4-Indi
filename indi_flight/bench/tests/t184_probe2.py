"""T184 probe 2: 10 ms hole check for a dup-absorbed gap on a slow controller-class topic (scratch)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import hole_report as hr  # noqa: E402

T0 = 10_000_000
END = T0 + 60_000_000
P = 20_000  # 50 Hz outer-loop topic
ts = np.arange(T0, END, P, dtype=np.int64)
ts = np.delete(ts, np.arange(1000, 1002))           # 40 ms gap (2 periods of 20 ms... dt=60 ms, k=3)
ts = np.delete(ts, np.arange(2000, 2001))           # 40 ms gap, k=2
ts = np.insert(ts, 2000, ts[2000])                  # one dup next to the k=2 gap
j = {"vehicle_local_position_setpoint": ts}
r = hr.analyse(j, T0, END)
row = [x for x in r["topics"] if x["topic"] == "vehicle_local_position_setpoint"][0]
print("gaps listed", row["count"], "max_hole_ms", row["max_hole_ms"], "missing", row["missing"],
      "pass", row["pass"], "class", row["class"])
ts2 = np.arange(T0, END, P, dtype=np.int64)
ts2 = np.delete(ts2, np.arange(2000, 2001))
ts2 = np.insert(ts2, 2000, ts2[2000])
r2 = hr.analyse({"vehicle_local_position_setpoint": ts2}, T0, END)
row2 = [x for x in r2["topics"] if x["topic"] == "vehicle_local_position_setpoint"][0]
print("no-absorb ref: gaps", row2["count"], "max_hole_ms", row2["max_hole_ms"], "pass", row2["pass"])
