"""S106 GNSS delay lag check (hook B after the timestamp fix).

For each sensor_gnss fix logged while the vehicle climbs or descends faster than 0.3 m/s, find the true generation
time t_gen by matching the fix altitude to the undelayed ground-truth altitude (linear interpolation, nearest crossing
before delivery). Reports per fix: delivery age = timestamp - t_gen (should be SIM_GZ_GPS_DLY, quantised up by <= 10 ms
plus the 1/30 s fix period alignment), and EKF time error = vehicle_gps_position.timestamp_sample - t_gen (should be
~0 when SENS_GNSS0_DELAY matches). Usage: python3 lagcheck.py flight.ulg SENS_GNSS0_DELAY_ms
Truth: vehicle_local_position_groundtruth ref_alt - z (gnss_truth is not logged).
"""
import sys
import numpy as np
from pyulog import ULog


def topic(u, name):
    for d in u.data_list:
        if d.name == name and d.multi_id == 0:
            return d.data
    return None


def alt_field(d):
    for k in ('altitude_msl_m', 'altitude_msl', 'alt'):
        if k in d:
            return np.asarray(d[k], dtype=float) * (1e-3 if k == 'alt' else 1.0)
    raise KeyError('no altitude field: %s' % sorted(d)[:40])


SENS_DLY_US = 0


def main(path):
    u = ULog(path)
    g, tr = topic(u, 'sensor_gnss'), topic(u, 'vehicle_local_position_groundtruth')
    if g is None or tr is None:
        print('missing topic: sensor_gnss', g is None, 'groundtruth', tr is None)
        return 2
    tt = tr['timestamp_sample'].astype(np.int64)
    at = np.asarray(tr['ref_alt'], dtype=float) - np.asarray(tr['z'], dtype=float)
    print('truth (vehicle_local_position_groundtruth) n %d rate %.1f Hz' % (len(tt), len(tt) / ((tt[-1] - tt[0]) / 1e6)))
    tg, sg, ag = g['timestamp'].astype(np.int64), g['timestamp_sample'].astype(np.int64), alt_field(g)
    print('sensor_gnss n %d, timestamp - timestamp_sample: max %d us (0 expected after fix)' % (len(tg), (tg - sg).max()))
    vz = np.gradient(at, tt / 1e6)
    rows = []
    for t_del, a in zip(tg, ag):
        m = (tt <= t_del) & (tt >= t_del - 600000)
        if m.sum() < 3 or np.min(np.abs(vz[m])) < 0.3:
            continue
        ts, as_ = tt[m], at[m]
        # last crossing of a between consecutive truth samples
        d = as_ - a
        idx = np.where(np.sign(d[:-1]) != np.sign(d[1:]))[0]
        if len(idx) == 0:
            continue
        i = idx[-1]
        t_gen = ts[i] + (ts[i + 1] - ts[i]) * (0 - d[i]) / (d[i + 1] - d[i])
        # EKF sample time per VehicleGPSPosition::resolveSampleTimestamp (driver sample < timestamp kept, else
        # timestamp - SENS_GNSS0_DELAY); vehicle_gps_position is not logged in these runs
        s_drv = int(sg[np.where(tg == t_del)[0][0]])
        ekf = (s_drv if s_drv < t_del else t_del - SENS_DLY_US) - t_gen
        rows.append((t_del / 1e6, (t_del - t_gen) / 1e3, ekf / 1e3))
    print('fixes in climb/descent: %d' % len(rows))
    for r in rows:
        print('  t %.2f s  delivery age %.1f ms  EKF sample-time error %.1f ms' % r)
    if rows:
        r = np.array(rows)
        print('median delivery age %.1f ms, median EKF time error %.1f ms' % (np.median(r[:, 1]), np.nanmedian(r[:, 2])))
    return 0


if __name__ == '__main__':
    SENS_DLY_US = int(sys.argv[2]) * 1000 if len(sys.argv) > 2 else 0
    sys.exit(main(sys.argv[1]))
