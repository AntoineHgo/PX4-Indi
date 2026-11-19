"""S133 T9: largest vehicle_thrust_setpoint z step within +-0.1 s of takeoff_status ->flight edge and hover_thrust_estimate valid edge. usage: t9_step_check.py flight.ulg"""
import sys, numpy as np
from pyulog import ULog
u = ULog(sys.argv[1]); L = {}
for d in u.data_list: L.setdefault(d.name, d)
th = L["vehicle_thrust_setpoint"].data; tt = th["timestamp"] / 1e6; z = -th["xyz[2]"]
ht = L["hover_thrust_estimate"].data; hv = np.where(ht["valid"] > 0)[0]
ts = L["takeoff_status"].data; st = ts["takeoff_state"]
print("takeoff_state values", sorted(set(st.tolist())))
edges = [("takeoff_state %d->%d" % (st[i-1], st[i]), ts["timestamp"][i] / 1e6) for i in range(1, len(st)) if st[i] != st[i-1]]
if len(hv): edges.append(("hover_thrust valid first", ht["timestamp"][hv[0]] / 1e6))
hover = np.median(z[(tt > tt[-1] - 40) & (tt < tt[-1] - 10)])
print("hover thrust (median late) %.4f" % hover)
for n, te in edges:
    m = (tt >= te - 0.1) & (tt <= te + 0.1)
    if m.sum() > 2:
        # largest step between samples 5 ms apart (any consecutive pair) and range over the window
        print("%-28s t=%.2f max consecutive step %.4f (%.2f%% hover), range %.4f (%.2f%%)" % (n, te, np.abs(np.diff(z[m])).max(), 100*np.abs(np.diff(z[m])).max()/hover, np.ptp(z[m]), 100*np.ptp(z[m])/hover))
