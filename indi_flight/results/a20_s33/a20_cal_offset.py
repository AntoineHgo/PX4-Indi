#!/usr/bin/env python3
"""A-20 (S33): CAL_BARO0_OFF and bias0 across the same-seed g16_set_s32 runs (logs only).

Per ULog: initial CAL_BARO0_OFF, any in-flight change, log start, first vehicle_gnss and sensor_baro
times, first estimator_baro_bias sample (bias0), median bias over 15-35 s, and the height equivalent of
the offset, off/(rho g), with rho from the median raw pressure over 15-35 s and an assumed ISA T.
Prints a table and a summary to stdout. Run from the repo root.
"""
import glob

import numpy as np
from pyulog import ULog

ROOT = 'indi_flight/results/g16_set_s32'
R_AIR, T_ISA, G = 287.05, 288.15, 9.81   # T is assumed; sim temperature is not logged
GRID = 20000.0 / 8192.0                    # 13-halving grid of BaroGNSSAltitudeOffset (Pa)


def main():
    rows = []
    for p in sorted(glob.glob(f'{ROOT}/speed*/*/r*/flight.ulg')):
        u = ULog(p, ['sensor_baro', 'estimator_baro_bias', 'vehicle_gnss', 'vehicle_local_position_groundtruth'])
        d = {x.name: x.data for x in u.data_list if x.multi_id == 0}
        off0 = float(u.initial_parameters.get('CAL_BARO0_OFF', np.nan))
        n_chg = sum(1 for (_, n, _) in u.changed_parameters if n == 'CAL_BARO0_OFF')
        sb, b, g = d['sensor_baro'], d['estimator_baro_bias'], d['vehicle_gnss']
        tb, ts = b['timestamp'] / 1e6, sb['timestamp'] / 1e6
        mb = (tb >= 15) & (tb <= 35)
        ms = (ts >= 15) & (ts <= 35)
        p_hold = float(np.median(sb['pressure'][ms])) if np.any(ms) else np.nan
        rho = p_hold / (R_AIR * T_ISA)
        med_bias = float(np.median(b['bias'][mb]))
        exp_m = off0 / (rho * G)
        rows.append(dict(name=p.split(ROOT + '/')[1].replace('/flight.ulg', ''), off0=off0, n_chg=n_chg,
                         t_log0=u.start_timestamp / 1e6, t_gnss0=g['timestamp'][0] / 1e6, t_baro0=ts[0],
                         bias0=float(b['bias'][0]), t_bias0=tb[0], med_bias=med_bias, exp_m=exp_m,
                         k=off0 / GRID, p_hold=p_hold))
    print(f"{'run':26s} {'off0':>6s} {'chg':>3s} {'t_log0':>6s} {'t_gnss0':>7s} {'t_baro0':>7s} {'bias0':>6s} "
          f"{'t_b0':>6s} {'med15-35':>8s} {'off/rhog':>8s} {'k':>6s}")
    for r in rows:
        print(f"{r['name']:26s} {r['off0']:6.2f} {r['n_chg']:3d} {r['t_log0']:6.2f} {r['t_gnss0']:7.2f} "
              f"{r['t_baro0']:7.2f} {r['bias0']:6.3f} {r['t_bias0']:6.2f} {r['med_bias']:8.3f} "
              f"{r['exp_m']:8.3f} {r['k']:6.2f}")
    off = np.array([r['off0'] for r in rows])
    med = np.array([r['med_bias'] for r in rows])
    b0 = np.array([r['bias0'] for r in rows])
    nz = off != 0
    slope, icpt = np.polyfit(off, med, 1)
    print(f"\nruns {len(rows)}, CAL_BARO0_OFF != 0 in {nz.sum()}, changes in flight {sum(r['n_chg'] for r in rows)}")
    print(f"corr(off0, median bias 15-35 s) = {np.corrcoef(off, med)[0, 1]:.3f}, "
          f"slope = {slope:.4f} m/Pa (intercept {icpt:.3f} m)")
    print(f"corr(off0, bias0) = {np.corrcoef(off, b0)[0, 1]:.3f}")
    print(f"mean hydrostatic 1/(rho g) at hold = {np.nanmean([1 / (r['p_hold'] / (R_AIR * T_ISA) * G) for r in rows]):.4f} m/Pa")
    print(f"max |k - round(k)| over offsets = {np.max(np.abs(np.array([r['k'] for r in rows]) - np.round([r['k'] for r in rows]))):.2e}")
    for r in rows:
        if abs(r['off0']) > 5:
            print(f"{r['name']}: median bias / (off/rhog) = {r['med_bias'] / r['exp_m']:.2f}")


if __name__ == '__main__':
    main()
