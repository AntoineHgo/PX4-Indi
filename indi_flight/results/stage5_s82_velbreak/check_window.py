import sys, numpy as np
from pyulog import ULog
s = [d for d in ULog(sys.argv[1], ["indi_pos_status"]).data_list][0].data
t = s["timestamp"] * 1e-6
for ax in range(3):
    d = np.asarray(s[f"inject[{ax}]"]); nz = np.flatnonzero(d != 0)
    print(ax, "n_nonzero", nz.size, "span", (t[nz[0]], t[nz[-1]]) if nz.size else None)
d = np.asarray(s["inject[2]"]); nz = np.flatnonzero(d != 0)
print("samples", t.size, "t", t[0], t[-1], "zeros inside window", int((d[nz[0]:nz[-1]+1] == 0).sum()))
u = np.asarray(s["a_c[2]"]); c = np.asarray(s["a_c_pre_inject[2]"])
print("max|u-c-d|", float(np.abs(u - c - d).max()), "max|d|", float(np.abs(d).max()))
