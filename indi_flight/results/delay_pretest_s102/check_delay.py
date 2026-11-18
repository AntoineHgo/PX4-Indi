#!/usr/bin/env python3
"""Measure IMU age (sensor_gyro) and actuator lag (actuator_motors -> esc_status rpm) on d0 and d5 ULogs.

Usage (inside docker): python3 check_delay.py <out>/d0/flight.ulg <out>/d5/flight.ulg
Window for lag: 4 s .. 19 s after first landed=false (same as pretest_gate.py --delay 4 --length 15).
"""
import sys
import numpy as np
from pyulog import ULog

GRID_US = 1250.0
HP_SAMPLES = 400   # 0.5 s moving-average high-pass
TRIM = 200         # samples trimmed at each end (filter edge effects)
MAXLAG = 32        # +-40 ms search in 1.25 ms steps


def ds(u, name):
    try:
        return u.get_dataset(name).data
    except Exception:
        return None


def hp(x):
    k = np.ones(HP_SAMPLES) / HP_SAMPLES
    return x - np.convolve(x, k, mode="same")


def xc_lag_ms(c, r):
    best_L, best_v = 0, -np.inf
    for L in range(-MAXLAG, MAXLAG + 1):
        if L >= 0:
            a, b = c[:len(c) - L], r[L:]
        else:
            a, b = c[-L:], r[:len(r) + L]
        v = np.dot(a, b) / len(a)
        if v > best_v:
            best_v, best_L = v, L
    return best_L * GRID_US / 1000.0


def analyse(path):
    print(f"== {path}")
    u = ULog(path, message_name_filter_list=["sensor_gyro", "actuator_motors", "esc_status",
                                              "vehicle_land_detected"])
    out = {}
    gyro = ds(u, "sensor_gyro")
    if gyro is not None:
        ts = gyro["timestamp"].astype(np.int64)
        m = gyro["multi_id"] == 0 if "multi_id" in gyro else np.ones(len(ts), bool)
        age = (ts - gyro["timestamp_sample"].astype(np.int64))[m].astype(float)
        out["gyro_age_us"] = (np.median(age), age.min(), age.max(), len(age))
        out["gyro_rate_hz"] = 1e6 / np.median(np.diff(ts[m]))
    am = ds(u, "actuator_motors")
    esc = ds(u, "esc_status")
    ld = ds(u, "vehicle_land_detected")
    if am is not None:
        out["act_rate_hz"] = 1e6 / np.median(np.diff(am["timestamp"]))
    if esc is not None:
        out["esc_rate_hz"] = 1e6 / np.median(np.diff(esc["timestamp"]))
    if am is None or esc is None or ld is None:
        print("  lag: topic missing", am is None, esc is None, ld is None)
        return out
    air = ld["timestamp"][ld["landed"] == 0]
    if len(air) == 0:
        print("  lag: no airborne sample")
        return out
    t0 = air[0] + 4e6
    t1 = t0 + 15e6
    g = np.arange(t0, t1, GRID_US)
    tc = am["timestamp"].astype(float)
    tr = esc["timestamp"].astype(float)
    lags = []
    for i in range(4):
        ck, rk = f"control[{i}]", f"esc[{i}].esc_rpm"
        if ck not in am or rk not in esc:
            print("  lag: missing field", ck, rk)
            return out
        c = hp(np.interp(g, tc, am[ck].astype(float)))[TRIM:-TRIM]
        r = hp(np.interp(g, tr, esc[rk].astype(float)))[TRIM:-TRIM]
        lags.append(xc_lag_ms(c, r))
    out["lag_ms_per_motor"] = lags
    out["lag_ms_median"] = float(np.median(lags))
    return out


def main(paths):
    res = {}
    for p in paths:
        res[p] = analyse(p)
        r = res[p]
        print(f"  rates Hz: sensor_gyro {r.get('gyro_rate_hz', float('nan')):.1f}  "
              f"actuator_motors {r.get('act_rate_hz', float('nan')):.1f}  "
              f"esc_status {r.get('esc_rate_hz', float('nan')):.1f}")
        if "gyro_age_us" in r:
            med, mn, mx, n = r["gyro_age_us"]
            print(f"  (a) IMU age us: median {med:.1f} min {mn:.1f} max {mx:.1f} n {n}")
        if "lag_ms_median" in r:
            print(f"  (b) lag ms per motor {[round(x, 2) for x in r['lag_ms_per_motor']]} "
                  f"median {r['lag_ms_median']:.2f}")
    d0, d5 = paths[0], paths[1] if len(paths) > 1 else None
    if d5 is None:
        return
    a0 = res[d0].get("gyro_age_us", (np.nan,))[0]
    a5 = res[d5].get("gyro_age_us", (np.nan,))[0]
    print(f"CHECK a d5 IMU age in [3750,6250] us: {'PASS' if 3750 <= a5 <= 6250 else 'FAIL'} ({a5:.1f})")
    print(f"CHECK a-neg d0 IMU age not ~5000 (|med|<1250): {'PASS' if abs(a0) < 1250 else 'FAIL'} ({a0:.1f})")
    if "lag_ms_median" in res[d0] and "lag_ms_median" in res[d5]:
        diff = res[d5]["lag_ms_median"] - res[d0]["lag_ms_median"]
        print(f"CHECK b lag d5-d0 in [3.75,6.25] ms: {'PASS' if 3.75 <= diff <= 6.25 else 'FAIL'} ({diff:.2f})")
    else:
        print("CHECK b: NOT COMPUTABLE")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("usage: check_delay.py D0_ULG D5_ULG")
    main(sys.argv[1:3])
