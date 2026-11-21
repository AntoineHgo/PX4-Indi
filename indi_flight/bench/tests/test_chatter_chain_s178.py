"""Synthetic self-test: a 33.3 Hz sinusoid injected in one channel must be found there and not in the others.
run: python3 indi_flight/bench/tests/test_chatter_chain_s178.py"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import chatter_chain_s178 as c

rng = np.random.default_rng(0)
t = np.arange(0, 80, 1 / 800.0)
chans = {k: rng.normal(0, 0.01, t.size) for k in "abcd"}
chans["b"] += 0.05 * np.sin(2 * np.pi * 33.3 * t) * ((t > 38) & (t < 52))
res = {k: c.line_stat(t, x, 38, 52, (30, 37)) for k, x in chans.items()}
assert abs(res["b"][0] - 33.3) < 0.6 and res["b"][1] > 50, res
assert all(res[k][1] < 10 for k in "acd"), res
# not present outside its window
assert c.line_stat(t, chans["b"], 18, 28, (30, 37))[1] < 10
# Nyquist guard: a topic logged at 40 Hz cannot show 33 Hz
tl = np.arange(0, 80, 1 / 40.0)
assert c.line_stat(tl, np.sin(tl), 38, 52, (30, 37)) is None
# collective vs differential: common-mode sinusoid shows in collective only
M = rng.normal(0, 0.01, (t.size, 4)) + 0.05 * np.sin(2 * np.pi * 33.3 * t)[:, None]
modes = c.motor_modes(M)
r = {k: c.line_stat(t, v, 0, 80, (30, 37)) for k, v in modes.items()}
assert r["collective"][1] > 50 and all(r[k][1] < 10 for k in ("diffA", "diffB", "diffC")), r
print("ok")
