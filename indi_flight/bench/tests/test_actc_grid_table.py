#!/usr/bin/env python3
"""Self-test: python3 indi_flight/bench/tests/test_actc_grid_table.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import actc_grid_table as g

H = ("cell\ttau_slow\tasym\tdir\tdly_ms\tframes\tseed\ttrue_up\ttrue_down\ttrue_mean\ttrue_slow\t"
     "est_up\test_down\test_sym\test_delay_ms\tpass\tflags\tsym_over_slow\tsym_over_mean\tresidual\tstatus")
R = [
    "a\t1\t1\t-\t0\t0\t1\t0.01\t0.01\t0.01\t0.01\t0.011\t0.009\t0.01\t2\t1\t\t0\t0\t0\tdone",
    "b\t1\t3\td\t10\t0\t1\t0.01\t0.03\t0.02\t0.03\t0.01\t0.033\t0.015\t12\t1\t\t0\t0\t0\tdone",
    "c\t1\t3\td\t10\t0\t1\t0.01\t0.03\t0.02\t0.03\t0.01\t0.03\t0.021\t13\t1\t\t0\t0\t0\tdone",
    "d\t1\t3\tu\t0\t0\t1\t0.03\t0.01\t0.02\t0.03\t0.03\t0.01\t0.02\t2\t0\tBAD\t0\t0\t0\tdone",
]
with tempfile.NamedTemporaryFile("w", suffix=".tsv", delete=False) as f:
    f.write(H + "\n" + "\n".join(R) + "\n")
rows = g.load(f.name)
os.unlink(f.name)
a, b, c, d = rows
assert abs(a["up"] - 1.1) < 1e-9 and abs(a["down"] - 0.9) < 1e-9
assert abs(b["r_slow"] - 0.5) < 1e-9 and abs(b["r_mean"] - 0.75) < 1e-9
assert abs(b["ddly"] - 2) < 1e-9 and abs(c["ddly"] - 3) < 1e-9
assert a["ok"] and not d["ok"] and d["cls"] == "3u" and a["cls"] == "1"
mn, mx, p95, n = g.stats([0.5, 0.7])
assert (mn, mx, n) == (0.5, 0.7, 2) and abs(p95 - 0.69) < 1e-9
assert g.stats([float("nan")]) is None
print("PASS")
