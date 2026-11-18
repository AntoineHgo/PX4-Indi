#!/usr/bin/env python3
"""Linear loop-transfer models of the rate loop for gate G2 (design/stage2_margins_s35.md sec 4 + 7, task T78).

Break point for INDI is M3a (torque setpoint): x = u = c + d (what the plant and the model see), y = c (returned signal),
y = -L x, so L = -c/u (same convention as margins_est.py).  GM/PM/DM are NOT recomputed here: margins_est.margins() is used.

Sampled-data model (exact, the same recursions as src/lib/indi_rate_control and src/lib/rate_control), T = 1/fs:
  plant     w' = G1 g eta m,  m' = (u_eff - m)/tau_r,  u_eff[k] = u[k-lat], u held over one cycle (exact ZOH):
            w[k+1] = w[k] + G1 g eta (c1 m[k] + c2 u_eff[k]),  m[k+1] = a_r m[k] + (1-a_r) u_eff[k],
            a_r = exp(-T/tau_r), c1 = tau_r (1-a_r), c2 = T - c1.   Sensors: w[k], m[k] sampled at k, used at k.
  filters   F  = LPF2p(gyro_fc) (PX4 biquad, bilinear Butterworth), alpha = first order AlphaFilter(dgyro_fc),
            rate = F w, a_f = alpha * (F[k] - F[k-1])/T  (VehicleAngularVelocity chain), H = alpha F.
  INDI      nu = -K F w;  t_act[k] = a_m t_act[k-1] + (1-a_m) u[k-1] (torque_allocated_prev = previous setpoint),
            t_f_model = H z^-d_m t_act;  t_f_meas = H z^-n (eta m);  blend b[k] = b[k-1] + ab (t_mod - t_meas - b[k-1]),
            ab = T/(Tb+T); t_f = t_f_model (meas=False) | t_f_meas (meas, Tb<=0) | t_f_meas + b (meas, Tb>0);
            u = t_f + (nu - a_f)/G1.   Analytic:  L = K F Pn + H Va - t_f/u   (Pn = w/(G1 u), Va = z-domain a/(G1 u)).
  PID       c = Kp (-F w) + I[k-1] - Kd a_f, I[k] = I[k-1] + Ki (-F w) T;  L = (Kp + Ki T z^-1/(1-z^-1)) F G1 Pn + Kd alpha F G1 Va.
Parameters (all keyword): fs, eta (delivered/allocated torque), g (G1_true/G1_set), Tb (blend, <=0 = pure measurement),
tau_r, tau_m, d_m (model delay samples), n (measurement delay samples), K, G1, gyro_fc, dgyro_fc, lat (extra command
latency samples, default 0), meas (use the measured torque path, default False = MC_INDI_W_MAX unset), eta_m (gain of the
model chain, 1 = the model does not know the fault; eta_m = eta makes model == measurement).

CLI:  python3 margins_models.py <out_dir>   -> a1_prediction.md, margins_models_table.md
"""
import argparse
import math
import os
import sys
from collections import deque

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import margins_est as ME  # noqa: E402

INDI_DEF = dict(eta=1.0, g=1.0, Tb=0.0, tau_r=0.033, tau_m=0.02, d_m=0, n=1, K=20.0, G1=320.0,
                gyro_fc=40.0, dgyro_fc=20.0, lat=0, meas=False, eta_m=1.0,
                fb_lead=0.0, att_p=0.0, sp_lead=False, att_lat=1)
# Firmware time constant of the setpoint-path lead filter (indi_rate_control.hpp kSetpointLeadTc)
SP_LEAD_TC = 0.01
# HEAD firmware, flown config of S57/S76/S77 (meas800.params): measured-rotor path, MC_INDI_LEAD 1 x K 20 x ACT_TC 0.05 -> c = 1,
# MC_ROLL_P 8 (airframe 4040_gz_quad5in; attitude path closed), setpoint-path lead on.  sp_lead=False reproduces the law before da64bc26b3.
# (Plain L_indi keeps its legacy defaults: no lead, no attitude path, so the G2 tables and the self-test are unchanged.)
HEAD_FLIGHT = dict(meas=True, Tb=0.0, n=1, tau_m=0.05, fb_lead=1.0, att_p=8.0, sp_lead=True, att_lat=1)
PRE_DA64 = dict(HEAD_FLIGHT, sp_lead=False)
PID_DEF = dict(eta=1.0, g=1.0, tau_r=0.033, Kp=0.03, Ki=0.06, Kd=0.0006, G1=320.0, gyro_fc=40.0, dgyro_fc=20.0, lat=0)


# ------------------------------------------------------------------------------------------ filters (PX4 coefficients)
def lpf2p_ba(fs, fc):
    """math::LowPassFilter2p: b (3), a (3, a0 = 1)."""
    ohm = math.tan(math.pi * fc / fs)
    k = 2.0 * math.cos(math.pi / 4.0) * ohm
    c = 1.0 + k + ohm * ohm
    b0 = ohm * ohm / c
    return (b0, 2 * b0, b0), (1.0, 2.0 * (ohm * ohm - 1.0) / c, (1.0 - k + ohm * ohm) / c)


def alpha_coef(fs, fc):
    """AlphaFilter::setCutoffFreq: alpha = Ts/(Ts + tau), tau = 1/(2 pi fc) (read from memory, see UNVERIFIED in the summary)."""
    T = 1.0 / fs
    return T / (T + 1.0 / (2 * math.pi * fc))


def tf_lpf2p(zi, fs, fc):
    b, a = lpf2p_ba(fs, fc)
    return (b[0] + b[1] * zi + b[2] * zi ** 2) / (a[0] + a[1] * zi + a[2] * zi ** 2)


def tf_alpha(zi, fs, fc):
    al = alpha_coef(fs, fc)
    return al / (1.0 - (1.0 - al) * zi)


# ------------------------------------------------------------------------------------------ analytic, sampled-data (z)
def _assemble(K, F, aF, Pn, Va, Tmod, Tmeas, Bl, meas):
    Tf = Tmod if not meas else Tmeas + Bl * (Tmod - Tmeas)
    return K * F * Pn + aF * Va - Tf  #BRK_mismatch


def L_indi(w, fs=800.0, **kw):
    """Discrete INDI rate loop broken at the torque setpoint (M3a). Evaluated at z = exp(j w T) on the array w [rad/s]."""
    p = dict(INDI_DEF)
    p.update(kw)
    w = np.asarray(w, float)
    T = 1.0 / fs
    zi = np.exp(-1j * w * T)  # z^-1
    a = math.exp(-T / p["tau_r"])
    c1 = p["tau_r"] * (1 - a)
    c2 = T - c1
    zl = zi ** p["lat"]
    Ar0 = (1 - a) * zi / (1 - a * zi)
    ge = p["g"] * p["eta"]
    Pn = ge * zl * (c1 * Ar0 + c2) * zi / (1 - zi)  # 1/(z-1) = z^-1/(1-z^-1)
    Va = ge * zl * zi * (c1 * Ar0 + c2) / T
    F = tf_lpf2p(zi, fs, p["gyro_fc"])
    aF = F * tf_alpha(zi, fs, p["dgyro_fc"])
    am = math.exp(-T / p["tau_m"])
    Tmod = aF * p["eta_m"] * (1 - am) * zi / (1 - am * zi) * zi ** p["d_m"]
    Tmeas = aF * p["eta"] * Ar0 * zl * zi ** p["n"]
    if p["Tb"] > 0:
        ab = T / (p["Tb"] + T)
        Bl = ab / (1 - (1 - ab) * zi)
    else:
        Bl = 0.0 * zi
    cl = p["fb_lead"]
    L = _assemble(p["K"], F, (1.0 + cl) * aF, Pn, Va, Tmod, Tmeas, Bl, p["meas"])
    if p["att_p"] > 0:
        # attitude path (A-34 / S78): rate_sp = -att_p * theta, theta[k+1] = theta[k] + T w[k] (+ att_lat samples of
        # setpoint latency).  nu = K (rate_sp - F w) gives K att_p theta; with sp_lead the setpoint-path lead of
        # da64bc26b3 adds cl * r_dot, r_dot = first order LPF (kSetpointLeadTc, discrete, alpha = T/(Tc+T)) of the
        # backward difference of rate_sp (the 1000 rad/s^2 clamp is nonlinear and ignored).
        als = T / (SP_LEAD_TC + T)
        D = als / (1.0 - (1.0 - als) * zi) * (1.0 - zi) / T
        lead = cl * D if p["sp_lead"] else 0.0
        L = L + (p["K"] + lead) * p["att_p"] * zi ** p["att_lat"] * T * zi / (1.0 - zi) * Pn
    return L


def L_pid(w, fs=800.0, **kw):
    """Discrete PX4 PID rate loop (P on rate error, I from the previous cycle, D on measured angular acceleration)."""
    p = dict(PID_DEF)
    p.update(kw)
    w = np.asarray(w, float)
    T = 1.0 / fs
    zi = np.exp(-1j * w * T)
    a = math.exp(-T / p["tau_r"])
    c1 = p["tau_r"] * (1 - a)
    c2 = T - c1
    zl = zi ** p["lat"]
    Ar0 = (1 - a) * zi / (1 - a * zi)
    ge = p["g"] * p["eta"]
    Pn = ge * zl * (c1 * Ar0 + c2) * zi / (1 - zi)
    Va = ge * zl * zi * (c1 * Ar0 + c2) / T
    F = tf_lpf2p(zi, fs, p["gyro_fc"])
    al = tf_alpha(zi, fs, p["dgyro_fc"])
    Ii = p["Ki"] * T * zi / (1 - zi)
    return (p["Kp"] + Ii) * F * p["G1"] * Pn + p["Kd"] * al * F * p["G1"] * Va


# ------------------------------------------------------------------------------------------ attitude loop (T194)
def _att_path(zi, fs, att_p, att_lat):
    """Attitude integrator and P gain seen from the rate setpoint: att_p z^-att_lat T z/(1-z)  (theta[k+1] = theta[k] + T w[k])."""
    T = 1.0 / fs
    return att_p * zi ** att_lat * T * zi / (1.0 - zi)


def _pn(zi, fs, p):
    """Pn = w/(G1 u) of the sampled plant (same expression as L_indi / L_pid)."""
    T = 1.0 / fs
    a = math.exp(-T / p["tau_r"])
    c1 = p["tau_r"] * (1 - a)
    c2 = T - c1
    Ar0 = (1 - a) * zi / (1 - a * zi)
    return p["g"] * p["eta"] * zi ** p["lat"] * (c1 * Ar0 + c2) * zi / (1 - zi)


def L_att_indi(w, fs=800.0, **kw):
    """Attitude loop broken at the rate setpoint (S86 break: x = rates_sp_applied, y = rates_sp_pre_inject, L = -Y/X).
    L_att = A_att * T_cl, A_att = att_p z^-att_lat T z/(1-z), T_cl = closed INDI rate loop from rate setpoint to measured rate
    w = (K + lead) Pn / (1 + L_rate), lead = fb_lead * D (sp_lead only), L_rate = L_indi with att_p = 0.  Defaults: HEAD_FLIGHT.
    Small-angle hover linearisation, no outer loop, roll/pitch only (yaw is not modelled)."""
    p = dict(INDI_DEF)
    p.update(HEAD_FLIGHT)
    p.update(kw)
    w = np.asarray(w, float)
    T = 1.0 / fs
    zi = np.exp(-1j * w * T)
    Lr = L_indi(w, fs, **dict(p, att_p=0.0))
    als = T / (SP_LEAD_TC + T)
    D = als / (1.0 - (1.0 - als) * zi) * (1.0 - zi) / T
    lead = p["fb_lead"] * D if p["sp_lead"] else 0.0
    Tcl = (p["K"] + lead) * _pn(zi, fs, p) / (1.0 + Lr)
    return _att_path(zi, fs, p["att_p"], p["att_lat"]) * Tcl


def outer_factor(w, Kp=0.95, Kv=1.8, Ki=0.4, Kd=0.2, fd=5.0):
    """Horizontal outer loop seen at the attitude break (A-36, keyed T195, design/t195_att_outer_key.md).
    Small-angle hover: v = g phi/s, x = v/s, phi_sp = a_sp/g with PositionControl P-PID (MPC_XY_P, MPC_XY_VEL_P/I/D_ACC,
    stock defaults), D on the velocity derivative low-passed at MPC_VELD_LP (fd).  The INDI acceleration increment
    cancels in the small-signal sense.  O = 1 + (Kv + Ki/s)(Kp + s)/s^2 + Kd F(s); EKF velocity lag not modelled."""
    s = 1j * np.asarray(w, float)
    F = 1.0 / (1.0 + s / (2 * np.pi * fd))
    return 1.0 + (Kv + Ki / s) * (Kp + s) / s ** 2 + Kd * F


def L_att_indi_outer(w, fs=800.0, outer=None, **kw):
    """L_att_indi times the closed horizontal outer loop (the S91 cells were flown in position mode)."""
    return L_att_indi(w, fs, **kw) * outer_factor(w, **(outer or {}))


def L_att_pid(w, fs=800.0, **kw):
    """Same break for the PX4 PID rate loop: T_cl = (Kp + Ki T z^-1/(1-z^-1)) G1 Pn / (1 + L_pid), L_att = A_att * T_cl.
    Parameters: PID_DEF (+ att_p 8, att_lat 1 from HEAD_FLIGHT).  No setpoint feed-forward in the PID law."""
    p = dict(PID_DEF)
    p.update(att_p=HEAD_FLIGHT["att_p"], att_lat=HEAD_FLIGHT["att_lat"])
    p.update(kw)
    w = np.asarray(w, float)
    T = 1.0 / fs
    zi = np.exp(-1j * w * T)
    Lr = L_pid(w, fs, **{k: v for k, v in p.items() if k not in ("att_p", "att_lat")})
    Ii = p["Ki"] * T * zi / (1 - zi)
    Tcl = (p["Kp"] + Ii) * p["G1"] * _pn(zi, fs, p) / (1.0 + Lr)
    return _att_path(zi, fs, p["att_p"], p["att_lat"]) * Tcl


# ------------------------------------------------------------------------------------------ analytic, continuous (s)
def _L_cont_s(s, fs=800.0, **kw):
    """Continuous approximation of L_indi at complex s: ZOH = T/2 delay, lags and delays as e^{-sT}-factors (note 4.1)."""
    p = dict(INDI_DEF)
    p.update(kw)
    T = 1.0 / fs
    wc = 2 * math.pi * p["gyro_fc"]
    F = 1.0 / (1.0 + math.sqrt(2.0) * s / wc + (s / wc) ** 2)
    aF = F / (1.0 + s / (2 * math.pi * p["dgyro_fc"]))
    ge = p["g"] * p["eta"]
    Ar = np.exp(-s * T * (0.5 + p["lat"])) / (1.0 + s * p["tau_r"])
    Am = p["eta_m"] * np.exp(-s * T * (0.5 + p["d_m"])) / (1.0 + s * p["tau_m"])
    Tmod = aF * Am
    Tmeas = aF * p["eta"] * Ar * np.exp(-s * T * p["n"])
    Bl = 1.0 / (1.0 + s * p["Tb"]) if p["Tb"] > 0 else 0.0 * s
    return _assemble(p["K"], F, aF, ge * Ar / s, ge * Ar, Tmod, Tmeas, Bl, p["meas"])


def L_indi_cont(w, fs=800.0, **kw):
    return _L_cont_s(1j * np.asarray(w, float), fs, **kw)


def L_pid_cont(w, fs=800.0, **kw):
    p = dict(PID_DEF)
    p.update(kw)
    s = 1j * np.asarray(w, float)
    T = 1.0 / fs
    wc = 2 * math.pi * p["gyro_fc"]
    F = 1.0 / (1.0 + math.sqrt(2.0) * s / wc + (s / wc) ** 2)
    al = 1.0 / (1.0 + s / (2 * math.pi * p["dgyro_fc"]))
    Ar = np.exp(-s * T * (0.5 + p["lat"])) / (1.0 + s * p["tau_r"]) * p["g"] * p["eta"]
    return (p["Kp"] + p["Ki"] / s + p["Kd"] * s * al) * F * p["G1"] * Ar / s


# ------------------------------------------------------------------------------------------ low-frequency polynomial
def a1_poly(eta, Tb, K=20.0):
    """Tb s^2 + eta (1 + K Tb) s + eta K: w_n, zeta, roots (note 4.3, restated with 7.3)."""
    wn = math.sqrt(eta * K / Tb)
    zeta = eta * (1 + K * Tb) / (2 * math.sqrt(eta * K * Tb))
    r = np.roots([Tb, eta * (1 + K * Tb), eta * K])
    return dict(wn=wn, zeta=zeta, roots=r, slow=r[np.argmin(np.abs(r.real))])


def lowfreq_pole(eta, Tb, K=20.0, start=None):
    """Dominant closed-loop pole found numerically (secant on 1 + L, complex s) from the continuous L_indi with all lags
    ~0 (1e-7 s, filters at 1e6 Hz), measured path n=0, model == nominal (eta_m = 1): i.e. the low-frequency L of 4.1."""
    kw = dict(eta=eta, Tb=Tb, K=K, tau_r=1e-7, tau_m=1e-7, n=0, d_m=0, lat=0, gyro_fc=1e6, dgyro_fc=1e6, meas=True, eta_m=1.0)
    f = lambda s: 1.0 + _L_cont_s(s, fs=1e7, **kw)
    r = a1_poly(eta, Tb, K)["roots"] if start is None else start
    out = []
    for r0 in r:
        s0, s1 = complex(r0), complex(r0) * (1 + 1e-3) + 1e-3
        f0, f1 = f(s0), f(s1)
        for _ in range(60):
            if f1 == f0:
                break
            s2 = s1 - f1 * (s1 - s0) / (f1 - f0)
            s0, f0, s1, f1 = s1, f1, s2, f(s2)
            if abs(s1 - s0) < 1e-12 * abs(s1):
                break
        out.append(s1)
    out = np.array(out)
    return out, out[np.argmin(np.abs(out.real))]


# ------------------------------------------------------------------------------------------ time-domain reference
class _Bq:
    def __init__(self, b, a):
        self.b, self.a = b, a
        self.x1 = self.x2 = self.y1 = self.y2 = 0.0

    def step(self, x):
        b, a = self.b, self.a
        y = b[0] * x + b[1] * self.x1 + b[2] * self.x2 - a[1] * self.y1 - a[2] * self.y2
        self.x2, self.x1, self.y2, self.y1 = self.x1, x, self.y1, y
        return y


class _Al:
    def __init__(self, al):
        self.al, self.y = al, 0.0

    def step(self, x):
        self.y += self.al * (x - self.y)
        return self.y


def _delay(n):
    return deque([0.0] * (n + 1), maxlen=n + 1)


def simulate_loop(d, fs, ctrl="indi", **kw):
    """Sample-by-sample difference-equation simulation of the broken loop; returns x = c + d (into the plant, after the
    break) and y = c (returned signal).  Written independently of the transfer-function code above."""
    p = dict(INDI_DEF if ctrl == "indi" else PID_DEF)
    p.update(kw)
    T = 1.0 / fs
    N = len(d)
    ar = math.exp(-T / p["tau_r"])
    c1 = p["tau_r"] * (1 - ar)
    c2 = T - c1
    Gp = p["G1"] * p["g"] * p["eta"]
    lb, la = lpf2p_ba(fs, p["gyro_fc"]), None
    lpf_w = _Bq(lpf2p_ba(fs, p["gyro_fc"])[0], lpf2p_ba(fs, p["gyro_fc"])[1])
    alpha_a = _Al(alpha_coef(fs, p["dgyro_fc"]))
    qlat = _delay(p["lat"])
    x, y = np.zeros(N), np.zeros(N)
    w = m = Fprev = 0.0
    dl = d.tolist()
    if ctrl == "indi":
        am = math.exp(-T / p["tau_m"])
        qmod, qmeas = _delay(p["d_m"]), _delay(p["n"])
        lpf_m, lpf_s = _Bq(*lpf2p_ba(fs, p["gyro_fc"])), _Bq(*lpf2p_ba(fs, p["gyro_fc"]))
        al_m, al_s = _Al(alpha_coef(fs, p["dgyro_fc"])), _Al(alpha_coef(fs, p["dgyro_fc"]))
        tact = uprev = blend = 0.0
        ab = T / (p["Tb"] + T) if p["Tb"] > 0 else 0.0
        for k in range(N):
            Fw = lpf_w.step(w)
            af = alpha_a.step((Fw - Fprev) / T)
            Fprev = Fw
            tact = am * tact + (1 - am) * uprev
            qmod.append(tact)
            tmod = al_m.step(lpf_m.step(p["eta_m"] * qmod[0]))
            if p["meas"]:
                qmeas.append(p["eta"] * m)
                tmeas = al_s.step(lpf_s.step(qmeas[0]))
                if p["Tb"] > 0:
                    blend += ab * ((tmod - tmeas) - blend)
                    tf = tmeas + blend
                else:
                    tf = tmeas
            else:
                tf = tmod
            c = tf + (-p["K"] * Fw - af) / p["G1"]
            xk = c + dl[k]
            y[k], x[k] = c, xk
            qlat.append(xk)
            u = qlat[0]
            w, m = w + Gp * (c1 * m + c2 * u), ar * m + (1 - ar) * u
            uprev = xk
    else:
        integ = 0.0
        for k in range(N):
            Fw = lpf_w.step(w)
            af = alpha_a.step((Fw - Fprev) / T)
            Fprev = Fw
            e = -Fw
            c = p["Kp"] * e + integ - p["Kd"] * af
            integ += p["Ki"] * e * T
            xk = c + dl[k]
            y[k], x[k] = c, xk
            qlat.append(xk)
            u = qlat[0]
            w, m = w + Gp * (c1 * m + c2 * u), ar * m + (1 - ar) * u
    return x, y


def L_timedomain(fs, ctrl="indi", Tp=5.0, n_per=6, discard=3, fmin=1.0, fmax_frac=0.4, per_decade=10, amp=0.01, **kw):
    """Inject a Schroeder multisine at the break, simulate, estimate L = -Y/X with margins_est.frf_periodic.
    fs*Tp must be an integer. Returns the estimator dict (keys f, w, L, accepted, ...)."""
    bins = ME.log_bins(fmin, fmax_frac * fs, Tp, per_decade)
    f = bins / Tp
    t, d = ME.multisine(f, amp, fs, Tp, n_per)
    x, y = simulate_loop(d, fs, ctrl, **kw)
    return ME.frf_periodic(d, x, y, fs, Tp, bins, discard=discard)


# ------------------------------------------------------------------------------------------ margins + tables
def margins_of(Lfun, fs, fmin=0.05, fmax_frac=0.45, npts=3000, **kw):
    f = np.geomspace(fmin, fmax_frac * fs, npts)
    w = 2 * np.pi * f
    return ME.margins(w, Lfun(w, fs, **kw))


def _n(x, fmt="%.1f"):
    return "-" if (x is None or (isinstance(x, float) and math.isnan(x))) else fmt % x


def _row(m):
    c = m["crossings"]
    fc = ", ".join("%.2f" % x["f_c"] for x in c) or "-"
    return "%s | %s | %s | %s | %s | %s" % (_n(m["gm_db"]), _n(m["pm_deg"]), _n(m["dm_s"] * 1e3, "%.1f"), fc, _n(m["Ms_db"]),
                                             "yes" if m["band_limited"] else "no")


def a1_table(K=20.0, fs=800.0):
    Tbs, etas = (0.03, 0.1, 0.3, 1.0), (1.0, 0.75, 0.5, 0.25)
    o = ["# A-1 prediction (T78): blend mode of the INDI rate loop, K = %g" % K, "",
         "Low-frequency polynomial Tb s^2 + eta (1 + K Tb) s + eta K: w_n = sqrt(eta K/Tb), zeta = eta (1+K Tb)/(2 sqrt(eta K Tb)).",
         "Overdamped cells (zeta >= 1) show the slow real pole in brackets.", "",
         "| Tb [s] | eta | w_n [rad/s] | zeta | slow pole [rad/s] |", "|---|---|---|---|---|"]
    for Tb in Tbs:
        for e in etas:
            r = a1_poly(e, Tb, K)
            o.append("| %g | %g | %.2f | %.2f | %.2f |" % (Tb, e, r["wn"], r["zeta"], r["slow"].real))
    o += ["", "## GM/PM/DM from the sampled-data L_indi at %g Hz (measured path + blend, n = 1, tau_m 0.02, tau_r 0.033, g = 1)" % fs, "",
          "| Tb [s] | eta | GM [dB] | PM [deg] | DM [ms] | f_c [Hz] | peak S [dB] | band-limited |", "|---|---|---|---|---|---|---|---|"]
    for Tb in Tbs:
        for e in etas:
            m = margins_of(L_indi, fs, eta=e, Tb=Tb, n=1, meas=True, K=K)
            o.append("| %g | %g | %s |" % (Tb, e, _row(m)))
    return "\n".join(o) + "\n"


def models_table():
    o = ["# Margins of the linear models (T78), roll axis", "",
         "Sampled-data L_indi / L_pid (cont.* = continuous e^{-sT} approximation). Defaults: tau_r 0.033, tau_m 0.02, K 20, G1 320,",
         "IMU_GYRO_CUTOFF 40, IMU_DGYRO_CUTOFF 20, d_m 0, lat 0; PID Kp 0.03 Ki 0.06 Kd 0.0006. DM requirement (note 3) = 2 Ts + n Ts.", "",
         "| controller | config | fs [Hz] | GM [dB] | PM [deg] | DM [ms] | f_c [Hz] | peak S [dB] | band-limited | DM req [ms] |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    cfgs = [("INDI", "model-only eta 1", dict(meas=False)),
            ("INDI", "model-only eta 0.5", dict(meas=False, eta=0.5)),
            ("INDI", "meas Tb 0, n 1, eta 1", dict(meas=True, Tb=0.0, n=1)),
            ("INDI", "meas+blend Tb 0.1, n 1, eta 1", dict(meas=True, Tb=0.1, n=1)),
            ("INDI", "meas+blend Tb 0.1, n 1, eta 0.5", dict(meas=True, Tb=0.1, n=1, eta=0.5))]
    for fs in (800.0, 400.0, 800.0 / 3):
        for ctrl, name, kw in cfgs:
            m = margins_of(L_indi, fs, **kw)
            o.append("| %s | %s | %.0f | %s | %.1f |" % (ctrl, name, fs, _row(m), (2 + kw.get("n", 1)) * 1e3 / fs))
        m = margins_of(L_pid, fs)
        o.append("| PID | roll gains | %.0f | %s | %.1f |" % (fs, _row(m), 2e3 / fs))
    m = margins_of(L_indi_cont, 800.0, meas=False)
    o.append("| INDI cont.* | model-only eta 1 | 800 | %s | - |" % _row(m))
    m = margins_of(L_pid_cont, 800.0)
    o.append("| PID cont.* | roll gains | 800 | %s | - |" % _row(m))
    return "\n".join(o) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out_dir")
    a = ap.parse_args(argv)
    os.makedirs(a.out_dir, exist_ok=True)
    for name, txt in (("a1_prediction.md", a1_table()), ("margins_models_table.md", models_table())):
        with open(os.path.join(a.out_dir, name), "w") as fh:
            fh.write(txt)
        print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
