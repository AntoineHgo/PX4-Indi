"""S54 A-27: frequency-domain model of the INDI rate law (indi_rate_control.cpp step 8) at 800 Hz, at two breaks:
M3a (d added to the command AND fed to the actuator model, u = c + d) and plant-only (d reaches the plant only).
Plant: first-order ZOH motor lag tau_p with one sample delay, alpha = (G1 + G2 (1 - z^-1)/dt) u_act, attitude P loop.
Filter H on t_f and a_f: 2nd-order Butterworth (bilinear) at fc. UNKEYED. usage: yaw_break_model_s54.py out.txt"""
import sys, numpy as np

def lpf2(z, fc, fs):
    K = np.tan(np.pi * fc / fs)
    a0 = 1 + np.sqrt(2) * K + K * K
    b = np.array([K * K, 2 * K * K, K * K]) / a0; a = np.array([1, 2 * (K * K - 1) / a0, (1 - np.sqrt(2) * K + K * K) / a0])
    zi = 1 / z
    return (b[0] + b[1] * zi + b[2] * zi ** 2) / (a[0] + a[1] * zi + a[2] * zi ** 2)

def lag(z, tau, dt, delay=1):
    a = np.exp(-dt / tau); zi = 1 / z
    return (1 - a) * zi ** delay / (1 - a * zi)

def loops(f, G1, G2, K, P, tau_p=0.033, tau_m=0.050, fc=30.0, fs=800.0, lead=1.0, law="code", g2p=1.0, taup_s=1.0):
    dt = 1 / fs; z = np.exp(1j * 2 * np.pi * f * dt); zi = 1 / z
    A, Am, H = lag(z, tau_p * taup_s, dt), lag(z, tau_m, dt), lpf2(z, fc, fs)
    integ = dt / (1 - zi)
    alpha = (G1 + g2p * G2 * (1 - zi) / dt) * A          # per unit plant input
    r = alpha * integ; psi = r * integ
    c = lead * K * tau_m
    if law == "code":   # step 8 as coded: static denominator G1 + G2/dt, t_f difference in the numerator
        D = G1 + G2 / dt; own = H * Am * (1 + (G2 / dt) * (1 - zi) / D)
    else:               # "lpf" (D-YAW-INV option c): increment = (nu - a_f) / (G1 + G2 (1 - z^-1)/dt), backward Euler
        D = G1 + G2 * (1 - zi) / dt; own = H * Am
    fb = (K * (-P * psi - r) - (1 + c) * H * alpha) / D   # nu and a_f terms per unit plant input
    L_m3a = -(own + fb)                     # model sees x
    L_plant = -fb / (1 - own)               # model sees y only (internal loop closed)
    return L_m3a, L_plant

def margins(f, L):
    mag = 20 * np.log10(np.abs(L)); ph = np.degrees(np.unwrap(np.angle(L)))
    out = {}
    i = np.where(np.diff(np.sign(mag)) != 0)[0]
    out["fc_hz"] = [round(float(f[k]), 2) for k in i]; out["pm_deg"] = [round(float(180 + ((ph[k] + 180) % 360 - 180) if False else ((ph[k] % 360) - 180)), 1) for k in i]
    out["Ms_db"] = round(float(np.max(-20 * np.log10(np.abs(1 + L)))), 1)
    return out

if __name__ == "__main__":
    f = np.logspace(-1, np.log10(60), 400); lines = []
    for name, G1, G2, K, P, law in [("roll", 1757, 0, 20, 6.5, "code"), ("yaw G2 27", 205, 27, 10, 2.8, "code"),
                                    ("yaw G2 0", 205, 0, 10, 2.8, "code"), ("yaw lpf27", 205, 27, 10, 2.8, "lpf")]:
        Lm, Lp = loops(f, G1, G2, K, P, law=law)
        for tag, L in (("M3a", Lm), ("plant-only", Lp)):
            pick = [np.argmin(abs(f - x)) for x in (0.1, 1.0, 10.0, 20.0)]
            lines.append(f"{name:10s} {tag:10s} |L| dB @0.1/1/10/20 Hz {[round(float(20*np.log10(abs(L[k]))),1) for k in pick]} "
                         f"arg {[round(float(np.degrees(np.angle(L[k]))),1) for k in pick]} {margins(f, L)}")
    for law in ("code", "lpf"):
        for g2p in (0.5, 2.0):
            for ts in (1.0, 2.0):
                Lm, Lp = loops(f, 205, 27, 10, 2.8, law=law, g2p=g2p, taup_s=ts)
                lines.append(f"mismatch yaw {law:4s} plant G2 x{g2p} tau x{ts}: M3a {margins(f, Lm)} plant-only {margins(f, Lp)}")
    open(sys.argv[1], "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
