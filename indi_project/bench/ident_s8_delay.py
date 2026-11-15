#!/usr/bin/env python3
"""Lag between the measured specific force a_f and the eRPM thrust t_f in an INDI POS ULog (review finding 2).

Cross-correlates the detrended a_f and t_f components logged in indi_pos_status. A positive lag means t_f lags
a_f by that many control cycles. t_f is logged after MC_INDIP_DLY cycles of delay on u, so the lag of the raw eRPM
thrust behind a_f is the peak lag minus that setting (negative: the eRPM leads). Only z is informative: the x/y
components of both signals follow the attitude and correlate at every lag. Usage: ident_s8_delay.py flight.ulg [dly_setting]
"""
import sys
import numpy as np
from pyulog import ULog

MAX_LAG = 8


def xcorr_lag(a, b):
    a = a - np.mean(a)
    b = b - np.mean(b)
    best, best_c = 0, -np.inf
    cs = {}
    for k in range(-MAX_LAG, MAX_LAG + 1):
        if k >= 0:
            c = np.dot(a[:len(a) - k], b[k:]) / (len(a) - k)
        else:
            c = np.dot(a[-k:], b[:len(b) + k]) / (len(b) + k)
        cs[k] = c / (np.std(a) * np.std(b) + 1e-12)
        if cs[k] > best_c:
            best, best_c = k, cs[k]
    return best, best_c, cs


def main():
    ulog = ULog(sys.argv[1], ['indi_pos_status'])
    dly = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    d = ulog.data_list[0].data
    ok = d['mean_u_valid'].astype(bool)
    for i, ax in enumerate('xyz'):
        a = d[f'a_f[{i}]'][ok]
        t = d[f't_f[{i}]'][ok]
        if ax == 'z':
            a = a - 9.80665  # a_f z includes gravity; offset removed by detrending anyway
        lag, c, cs = xcorr_lag(a, t)
        print(f'{ax}: peak lag {lag:+d} cycles (corr {c:.2f}), raw eRPM lags a_f by {lag - dly:+d} cycles; '
              f'corr at -4..+1: ' + ' '.join(f'{cs[k]:.2f}' for k in range(-4, 2)))


if __name__ == '__main__':
    main()
