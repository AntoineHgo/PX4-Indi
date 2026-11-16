"""S49: falsification sweep of the D-RATE-LEAD candidate with unmodelled plant command delay (lat samples).
Reuses lead_model_s48.L_lead (keyed S48 T101 on PM). Usage: lead_delay_sweep_s49.py <out.md>"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lead_model_s48 as LM  # noqa: E402

def main(path):
    o = ["# S49 lead candidate vs unmodelled delay (model only, roll, P_att 8, tau_r = tau_m = tau_c 0.033)", "",
         "Stop rule (route check 49): PM < 50 deg or GM < 8 dB at 400 Hz -> stop D-RATE-LEAD.", "",
         "| case | PM deg | f_c Hz | GM dB | DM ms |", "|---|---|---|---|---|"]
    b = dict(tau_r=0.033, tau_m=0.033, meas=False)
    for fs in (800.0, 400.0, 250.0):
        for ms in (0.0, 3.0, 5.0):
            lat = int(round(ms * 1e-3 * fs))
            for K in (20.0, 30.0, 40.0):
                for tc in (0.0, 0.033):
                    LM.row(o, "fs%d lat %d (%.1f ms) K%d tau_c %g" % (fs, lat, 1e3 * lat / fs, K, tc), LM.L_lead,
                           fs=fs, P_att=8.0, tau_c=tc, **dict(b, K=K, lat=lat))
    open(path, "w").write("\n".join(o) + "\n"); print("\n".join(o))

if __name__ == "__main__":
    main(sys.argv[1])
