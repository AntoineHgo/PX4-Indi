import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from g3_line_trace_s191 import ls_fit, window_scan

def test():
    t = np.sort(np.random.default_rng(0).uniform(0, 20, 3000))   # irregular native samples
    q = 5 * np.sin(2 * np.pi * 2.0 * t); p = 0.5 * np.sin(2 * np.pi * 2.0 * t + np.radians(30))
    rq, rp = ls_fit(t, q, 2.0, 5, 15), ls_fit(t, p, 2.0, 5, 15)
    assert abs(abs(rq) - 5) < 0.05 and abs(abs(rp) - 0.5) < 0.01
    assert abs(np.degrees(np.angle(rp / rq)) - 30) < 1.0       # positive = leads
    tb = np.arange(0, 20, 1 / 267.0); big = 3.0 * np.sin(2 * np.pi * 0.25 * tb + 1.0) + 0.1 * np.sin(2 * np.pi * 1.45 * tb)   # slow trajectory + small line
    assert abs(abs(ls_fit(tb, big, 1.45, 5, 13)) - 0.1) < 0.02
    tu = np.arange(0, 20, 1 / 267.0); xu = 5 * np.sin(2 * np.pi * 2.0 * tu)
    w = window_scan(tu, xu, 1.5, 3.0)
    assert all(abs(f - 2.0) < 0.3 and abs(r - 5 / np.sqrt(2)) < 0.4 for _, f, r in w)
if __name__ == "__main__": test(); print("ok")
