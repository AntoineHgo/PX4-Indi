#!/usr/bin/env python3
"""S48: M3a roll break with attitude P closed: PID reference and INDI with a rate-prediction lead.
INDI lead (candidate, not in firmware): nu = K (rate_sp - F w) - K tau_c a_f  -> rate term K F Pn (1 + P/s) + K tau_c alpha F Va,
Va = Pn (1 - z^-1)/T. PID: L = (Kp + Ki/s)(1 + P/s) F G1 Pn + Kd alpha F G1 Va (D on measured accel), G1 = plant 1757.
Usage: lead_model_s48.py <out.md>"""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import att_loop_model_s48 as A, margins_models as MM  # noqa: E402

def att(zi, fs, P):
    return 1.0 + P / fs * zi / (1 - zi)

def L_lead(w, fs=800.0, P_att=8.0, tau_c=0.0, **kw):
    p = dict(MM.INDI_DEF); p.update(kw)
    L0 = MM.L_indi(w, fs=fs, **p); p2 = dict(p); p2["K"] = 0.0
    Lk0 = MM.L_indi(w, fs=fs, **p2); rt = L0 - Lk0
    zi = np.exp(-1j * np.asarray(w, float) / fs)
    lead = rt * tau_c * MM.tf_alpha(zi, fs, p["dgyro_fc"]) * (1 - zi) * fs
    return Lk0 + rt * att(zi, fs, P_att) + lead

def L_pid_att(w, fs=800.0, P_att=8.0, **kw):
    p = dict(MM.PID_DEF); p.update(kw)
    zi = np.exp(-1j * np.asarray(w, float) / fs)
    pk = dict(p); pk.update(Kd=0.0); Lpi = MM.L_pid(w, fs=fs, **pk)
    pd = dict(p); pd.update(Kp=0.0, Ki=0.0); Ld = MM.L_pid(w, fs=fs, **pd)
    return Lpi * att(zi, fs, P_att) + Ld

def row(out, name, fun, **kw):
    m = A.marg(fun, **kw); c = m["crossings"]
    fc = c[0]["f_c"] if c else float("nan")
    out.append("| %s | %.1f | %.2f | %.1f | %.1f |" % (name, m["pm_deg"], fc, m["gm_db"], 1e3 * m["dm_s"]))

def main(path):
    o = ["# S48 M3a roll break with attitude P closed: PID reference and INDI lead candidate", "",
         "| case | PM deg | f_c Hz | GM dB | DM ms |", "|---|---|---|---|---|"]
    for P in (8.0, 5.0):
        row(o, "PID airframe gains G1 1757 P%g" % P, L_pid_att, P_att=P, G1=1757.0)
    b = dict(tau_r=0.033, tau_m=0.033, meas=False)
    for K in (20, 40, 60, 80):
        for tc in (0.0, 0.033):
            for P in (8.0, 5.0):
                row(o, "INDI K%d tau_c %g P%g" % (K, tc, P), L_lead, P_att=P, tau_c=tc, **dict(b, K=float(K)))
    for fs in (400.0, 250.0):
        row(o, "INDI fs%d K40 tau_c 0.033 P8" % fs, L_lead, fs=fs, P_att=8.0, tau_c=0.033, **dict(b, K=40.0))
    open(path, "w").write("\n".join(o) + "\n"); print("\n".join(o))

if __name__ == "__main__":
    main(sys.argv[1])
