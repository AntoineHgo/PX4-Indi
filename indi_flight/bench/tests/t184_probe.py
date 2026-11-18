"""T184 second-key probes for hole_report.py (scratch, numpy only). python3 -B this file."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import hole_report as hr  # noqa: E402

T0 = 10_000_000
P = 1250
END = T0 + 120_000_000


def base(n=None):
    end = END if n is None else T0 + n * P
    return np.arange(T0, end, P, dtype=np.int64)


def run(m, end=END, name="actuator_motors"):
    j = {name: np.sort(m)}
    r = hr.analyse(j, T0, end)
    row = [x for x in r["topics"] if x["topic"] == name][0]
    return row


def show(label, row):
    print(f"{label:52s} missing={row['missing']:3d} count_based={row['missing_count_based']:3d} "
          f"count={row['count']} tol={row['count_tol']} disagree={row['count_disagree']} pass={row['pass']}")


# A. isolated genuine drop, no dup anywhere
m = np.delete(base(), 20000)
show("A isolated drop, no dup", run(m))

# B. genuine drop with an UNRELATED dup 4 samples later (inside DUP_WINDOW)
m = np.delete(base(), 20000)
m = np.insert(m, 20003, m[20003])     # dup stamp ~4 samples after the drop
show("B drop + dup 4 samples away", run(m))

# C. genuine drop with dup 9 samples away (outside window)
m = np.delete(base(), 20000)
m = np.insert(m, 20009, m[20009])
show("C drop + dup 9 samples away", run(m))

# D. two gaps, one dup between them (single dup must absorb only one)
m = np.delete(base(), [20000, 20004])
m = np.insert(m, 20002, m[20002])
show("D two drops 4 apart, one dup between", run(m))

# E. two drops far apart, one far dup each (balanced): gm=2, cm=0 -> diff 2 -> FAIL?
m = np.delete(base(), [20000, 60000])
m = np.insert(m, [30000, 70000], m[[30000, 70000]])
show("E 2 drops + 2 far dups", run(m))

# F. one far dup only (drop + unpaired dup far away): diff 1 tolerated
m = np.delete(base(), 20000)
m = np.insert(m, 70000, m[70000])
show("F 1 drop + 1 far dup", run(m))

# G. dup stolen by earlier drop from a later publish-jitter pair
m = base().copy()
m = np.delete(m, 20000)                       # drop at ~20000
q = 20010                                     # jitter pair: dup then 2-period gap, 10 samples later
m[q + 1] = m[q]
m[q + 2] = m[q] + 2 * P
m = np.sort(m)
row = run(m)
show("G drop@20000 + jitter pair@20010 (x-check)", row)

# H. jitter pair alone, no drop (must be 0 missing)
m = base().copy()
m[20001] = m[20000]
m[20002] = m[20000] + 2 * P
m = np.sort(m)
show("H jitter pair alone", run(m))

# I. one drop with dup in window but the gap is 3-period (2 missing) and one dup
m = np.delete(base(), [20000, 20001])
m = np.insert(m, 20005, m[20005])
show("I 2 consecutive drops + 1 dup nearby", run(m))

# J. tolerance boundary: 120 s 800 Hz, 3000 paired jitter pairs (stride 32, net 0) plus k far unpaired dups
def jitter_log(k):
    m = base().copy()
    a = 31 * np.arange(3050) + 2                 # pair sites, >8 samples apart from each other
    m[a + 1] = m[a]                              # sample a+1 re-stamped as a (dup), a+2 keeps stamp -> 2-period gap
    far = 31 * (np.arange(k) + 1000) + 15                # far dup sites, >8 samples from every pair gap
    m = np.insert(m, far, m[far])
    return m


for k in (0, 3, 4, 5, 6):
    row = run(jitter_log(k))
    show(f"J 3000 pairs + {k} unpaired dups", row)

# K. wrong-rate segment: second half of a 120 s log stamped at 1251 us (median stays 1250)
m = np.concatenate([np.arange(T0, T0 + 60_000_000, P), np.arange(T0 + 60_000_000, END, 1251)]).astype(np.int64)
show("K half log at 1251 us vs median 1250", run(m))
# K2: 0.02 % rate error on a 120 s log
m = np.concatenate([np.arange(T0, T0 + 60_000_000, P), np.arange(T0 + 60_000_000, END, 1250.3)]).astype(np.int64)
show("K2 half log at 1250.3 us", run(m))
