"""S55 D-YAW-INV: extend the keyed S54 yaw model (bench/yaw_break_model_s54.py, loops() unchanged, imported) with
model ACT_TC mismatch (tau_m vs plant tau_p) and controller rate (250/400/800 Hz). Wrap-free margins:
PM = 180 - |arg L| at each |L| = 1 crossing (sign of the margin not resolved: read with Ms), GM = -|L| dB at each
real-axis crossing with Re L < 0. Ms = max |1/(1+L)| dB is the primary measure. UNKEYED.
usage: yaw_break_model_s55.py out.txt"""
import sys, numpy as np
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from yaw_break_model_s54 import loops

def margins2(f, L):
    mag = 20 * np.log10(np.abs(L)); ang = np.degrees(np.angle(L))
    ic = np.where(np.diff(np.sign(mag)) != 0)[0]
    ip = [k for k in np.where(np.diff(np.sign(L.imag)) != 0)[0] if L.real[k] < 0]
    return {"fc_hz": [round(float(f[k]), 2) for k in ic], "pm": [round(float(180 - abs(ang[k])), 1) for k in ic],
            "gm_db": [round(float(-mag[k]), 1) for k in ip], "Ms_db": round(float(np.max(-20 * np.log10(np.abs(1 + L)))), 1)}

if __name__ == "__main__":
    lines = []
    for fs in (250.0, 400.0, 800.0):
        f = np.logspace(-1, np.log10(min(60, 0.45 * fs)), 600)
        for law in ("code", "lpf"):
            for tm_s in (0.5, 1.0, 1.5, 2.0):      # model ACT_TC / plant tau (plant tau_p 33 ms, model nominal 50 ms)
                for g2p in (0.5, 1.0, 2.0):
                    for ts in (1.0, 2.0):
                        tau_m = 0.033 * tm_s
                        Lm, Lp = loops(f, 205, 27, 10, 2.8, tau_m=tau_m, fs=fs, law=law, g2p=g2p, taup_s=ts)
                        lines.append(f"fs {fs:4.0f} {law:4s} tau_m/tau_p0 x{tm_s} plantG2 x{g2p} plant tau x{ts}: "
                                     f"M3a {margins2(f, Lm)} | plant-only {margins2(f, Lp)}")
    open(sys.argv[1], "w").write("\n".join(lines) + "\n")
    # summary: worst Ms per fs/law
    import re
    for fs in ("250", "400", "800"):
        for law in ("code", "lpf"):
            sel = [l for l in lines if l.startswith(f"fs {fs:>4s} {law}")]
            ms = [float(x) for l in sel for x in re.findall(r"Ms_db': (-?[\d.]+)", l.split("|")[0])]
            msp = [float(x) for l in sel for x in re.findall(r"Ms_db': (-?[\d.]+)", l.split("|")[1])]
            print(f"fs {fs} {law}: M3a Ms dB min/max {min(ms)}/{max(ms)}  plant-only Ms min/max {min(msp)}/{max(msp)}")
