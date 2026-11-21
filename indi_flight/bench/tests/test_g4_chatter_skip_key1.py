"""Synthetic self-test of the Q18 A touchdown skip. run (needs scipy, docker):
  python3 indi_flight/bench/tests/test_g4_chatter_skip_key1.py
Break check: G4_SKIP_DISABLE=1 python3 ... must FAIL."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import g4_chatter_skip_key1 as s

fs = 800.0; rng = np.random.default_rng(1)
t = np.arange(0, 60, 1 / fs)
GC, LD = 40.0, 40.7
SK = s.skip_interval(GC, LD)

def run(t0, t1, amp=0.01, f=20.0):
    cmd = rng.normal(0, 0.001, (t.size, 4))
    cmd[:, 1] += amp * np.sin(2 * np.pi * f * t) * ((t >= t0) & (t < t1))   # line RMS 7e-3 >> 5e-4
    return s.scan(t, cmd, 0.0, 59.9, SK)

# edge logic
assert SK == (39.0, 41.7), SK
assert s.skip_interval(None, None) is None and s.skip_interval(40.0, None) is None
# landing detector from edges: ground contact flickers early (before takeoff), final rise at 40.0
tt = np.array([0, 1, 5, 20, 40.0, 40.7, 50]); gc = np.array([1, 0, 0, 0, 1, 1, 1]); ld = np.array([1, 0, 0, 0, 0, 1, 1])
assert s.edges_to_landing(tt, gc, ld) == (40.0, 40.7)
assert s.edges_to_landing(tt[:4], gc[:4], ld[:4]) == (None, None)   # no landing -> nothing skipped

# 1. line only inside the land window (t in 39.5..41.5 sits in every window that is not skipped?) -> no flag
v, rows = run(39.0, 42.0)
assert not v["chatter"], (v, [r for r in rows if r[7]][:3])
assert v["skipped_windows"] > 0
# the unskipped windows must be clean of flags
assert not any(r[7] and not r[2] for r in rows)
# 2. same line clearly outside (20..32 s) -> flag
v, rows = run(20.0, 32.0)
assert v["chatter"] and any(abs(r[4] - 20.0) < 0.5 for r in rows if r[7] and not r[2]), v
# 3. window overlap edges (hop 1 s, 4 s windows from 0): window [35,39] touches skip start 39.0 -> NOT skipped; [36,40] skipped
w = {(round(r[0]), round(r[1])): r[2] for r in rows}
assert w[(35, 39)] is False and w[(36, 40)] is True
#    window [41.7+..] : [42,46] is not skipped, [41,45] overlaps (41 < 41.7) skipped
assert w[(41, 45)] is True and w[(42, 46)] is False
# 4. line right at the edge, ending at 39.0 and starting after: only windows overlapping the skip are lost
v, rows = run(30.0, 39.0)
assert v["chatter"], v          # windows [30,34],[31,35],... [35,39] are kept: 6 consecutive flags
# 5. a line that exists only just after the skip (42.0..48.0) still flags
v, rows = run(42.0, 50.0)
assert v["chatter"], v
print("ok")
