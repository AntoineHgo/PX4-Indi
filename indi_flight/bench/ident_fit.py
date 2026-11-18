#!/usr/bin/env python3
"""Offline fit of the INDI control effectiveness G1 of one axis from an M3a injection hover log.

    python3 ident_fit.py flight.ulg --axis roll --t0 25 --t1 75

Model: alpha(t) = G1 * u_meas(t) + c, alpha = angular acceleration [rad/s^2] (differentiated gyro),
u_meas = actuator_torque_measured (normalised torque, (omega/W_MAX)^2 space, the units of G1 in the controller).
Level u (not increment) is regressed; with the intercept this equals the increment form.
Instrument = injected excitation indi_rate_status.inject (d), lagged copies. Regressand, regressor and instrument
go through the SAME FIR filter (condition iii). All timestamps are timestamp_sample (simulation time).
Method: ident_iv.py (iv_effectiveness, latency_by_xcorr).
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ident_iv as iv  # noqa: E402

AXES = {"roll": 0, "pitch": 1, "yaw": 2}


def fit_axis(t_gyro, omega, t_u, u, t_z, z, t0, t1, sat=None, t_sat=None, ntaps=15, fs=800.0,
             lags=None, hac_lags=400, max_lag=40, compensate_latency=True):
    """Core pipeline on already extracted arrays (seconds, SI). Returns dict of results.

    Pass 1 fits and measures the telemetry latency of u_meas by xcorr (latency_by_xcorr). With compensate_latency
    the regressor time base is shifted by that lag (x(t) = u_meas(t + lag), linear interpolation) and the fit is
    repeated (pass 2, reported; lag from the J scan); the pass 1 values are kept as g1_nocomp / ols_nocomp. The instrument is the
    command-side injection and is never shifted.
    """
    r1 = _fit_once(t_gyro, omega, t_u, u, t_z, z, t0, t1, sat, t_sat, ntaps, fs, lags, hac_lags, max_lag)
    if not compensate_latency:
        return r1
    # The xcorr lag is biased by feedback when the disturbance dominates alpha (u then correlates with the
    # disturbance, not only with the exogenous injection). The compensation lag is therefore the one that
    # minimises the Hansen J of the IV fit (exogenous instrument; J is large when y and x are misaligned).
    cand = np.arange(0.0, 8.01, 0.5) / fs
    js = [(_fit_once(t_gyro, omega, np.asarray(t_u, float) - c, u, t_z, z, t0, t1, sat, t_sat, ntaps, fs, lags,
                     40, max_lag)["j"], c) for c in cand]
    jv = np.array([j for j, _ in js])
    i = int(np.argmin(jv))
    c = cand[i]
    if 0 < i < len(cand) - 1 and jv[i - 1] - 2 * jv[i] + jv[i + 1] > 0:
        c += 0.5 / fs * 0.5 * (jv[i - 1] - jv[i + 1]) / (jv[i - 1] - 2 * jv[i] + jv[i + 1])
    r2 = _fit_once(t_gyro, omega, np.asarray(t_u, float) - c, u, t_z, z, t0, t1, sat, t_sat, ntaps, fs,
                   lags, hac_lags, max_lag)
    r2.update(g1_nocomp=r1["g1"], ols_nocomp=r1["ols"], lat_pass1_s=r1["lat_s"], lat_pass1_samples=r1["lat_samples"],
              f_nocomp=r1["f"], j_nocomp=r1["j"], comp_lag_s=float(c), comp_lag_samples=float(c * fs))
    return r2


def _fit_once(t_gyro, omega, t_u, u, t_z, z, t0, t1, sat, t_sat, ntaps, fs, lags, hac_lags, max_lag):
    dt = 1.0 / fs
    t_grid = np.arange(t0, t1, dt)
    taps = iv.smooth_taps(ntaps)
    y, x, zz, excl = iv.prepare_regression(t_gyro, omega, t_u, u, t_grid, taps, saturated=sat, t_sat=t_sat,
                                           z=z, t_z=t_z)
    if lags is None:
        lags = list(range(0, 33, 2))
    r = iv.iv_effectiveness(y, x, zz, lags=lags, exclude=excl, hac_lags=hac_lags)
    ok = np.isfinite(y) & np.isfinite(x)
    lat = iv.latency_by_xcorr(np.where(excl, np.nan, y), np.where(excl, np.nan, r["beta"][0] * x), dt, max_lag)
    return dict(g1=float(r["beta"][0]), se=float(r["se"][0]), ci95=1.96 * float(r["se"][0]),
                f=float(r["f_first"][0]), n=int(r["n"]), excl_frac=float(excl[ok].mean()) if ok.any() else 1.0,
                ols=float(r["ols"]["beta"][0]), ols_se=float(r["ols"]["se"][0]), intercept=r["intercept"],
                j=r["j_stat"], j_df=r["j_df"], lat_samples=lat["lag_samples"], lat_s=lat["lag_s"],
                lat_peak=lat["peak"], dt=dt)


def load(path, axis):
    from pyulog import ULog
    ul = ULog(path, ["sensor_gyro", "actuator_torque_measured", "indi_rate_status", "control_allocator_status"])
    d = {m.name: m.data for m in ul.data_list}
    k = AXES[axis]
    ts = lambda m: np.asarray(m["timestamp_sample"], float) * 1e-6  # noqa: E731
    g, a, s, c = d["sensor_gyro"], d["actuator_torque_measured"], d["indi_rate_status"], d["control_allocator_status"]
    tg = ts(g)
    t_start = ul.start_timestamp * 1e-6
    out = dict(t_gyro=tg, omega=np.asarray(g["xyz"[k]], float), t_u=ts(a),
               u=np.asarray(a["torque[%d]" % k], float), t_z=ts(s), z=np.asarray(s["inject[%d]" % k], float),
               t_sat=np.asarray(c["timestamp"], float) * 1e-6,
               sat=~np.asarray(c["torque_setpoint_achieved[%d]" % k] if ("torque_setpoint_achieved[%d]" % k) in c
                               else c["torque_setpoint_achieved"], bool), t_log0=t_start)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ulg")
    ap.add_argument("--axis", default="roll", choices=list(AXES))
    ap.add_argument("--t0", type=float, required=True, help="window start, log seconds (since log start)")
    ap.add_argument("--t1", type=float, required=True)
    ap.add_argument("--ntaps", type=int, default=15)
    a = ap.parse_args(argv)
    D = load(a.ulg, a.axis)
    t0l = D.pop("t_log0")
    for key in ("t_gyro", "t_u", "t_z", "t_sat"):
        D[key] = D[key] - t0l
    r = fit_axis(D["t_gyro"], D["omega"], D["t_u"], D["u"], D["t_z"], D["z"], a.t0, a.t1,
                 sat=D["sat"], t_sat=D["t_sat"], ntaps=a.ntaps)
    print(f"axis {a.axis}  window {a.t0}-{a.t1} s  taps {a.ntaps}")
    print(f"G1 (IV)        {r['g1']:.1f} rad/s^2  se {r['se']:.1f}  95% CI +-{r['ci95']:.1f} ({100*r['ci95']/abs(r['g1']):.1f} %)")
    print(f"G1 (OLS)       {r['ols']:.1f}  se {r['ols_se']:.1f}")
    print(f"first-stage F  {r['f']:.1f}")
    print(f"samples        {r['n']}  excluded (saturated) fraction {r['excl_frac']:.4f}")
    print(f"Hansen J       {r['j']:.1f} (df {r['j_df']})  intercept {r['intercept']:.3f}")
    if "g1_nocomp" in r:
        print(f"pass 1 (no latency compensation): G1 IV {r['g1_nocomp']:.1f}  OLS {r['ols_nocomp']:.1f}  F {r['f_nocomp']:.1f}"
              f"  J {r['j_nocomp']:.1f}  xcorr lag {r['lat_pass1_samples']:.2f} samples = {1e3*r['lat_pass1_s']:.2f} ms")
        print(f"compensation lag (min Hansen J scan) {r['comp_lag_samples']:.2f} samples = {1e3*r['comp_lag_s']:.2f} ms")
    print(f"latency xcorr (after compensation, residual) {r['lat_samples']:.2f} samples = {1e3*r['lat_s']:.2f} ms (peak corr {r['lat_peak']:.3f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
