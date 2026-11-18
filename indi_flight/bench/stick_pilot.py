"""Simulated pilot for the manual-stick scenarios (S118, D-G3-STICK-PILOT; design/i118_stick_pilot.md).

Pure Python, no MAVLink. A human holding a stabilized / acro stick closes two slow loops the open-loop stick profile lacks:
- altitude (stabilized and acro): PI on altitude error plus velocity damping, as a thrust correction around the profile thrust;
- levelling (acro only): roll / pitch rate-stick correction = -k_level * attitude, converted to stick units with the acro map.
altctl / posctl hold altitude and attitude themselves: the pilot returns zeros there.

Units: thrust corrections are collective thrust in 0..1 (PX4 normalized thrust), added to the profile thrust before the
mode's thrust-to-stick map (stick_profile.thrust_to_stick); rate-stick corrections are MANUAL_CONTROL fractions in [-1, 1].
Sign conventions: z_up = -LOCAL_POSITION_NED.z, vz_up = -vz, roll right positive, pitch nose up positive. Acro map of PX4
(McIndiRateControl.cpp, MulticopterRateControl.cpp): roll rate = superexpo(y) * MC_ACRO_R_MAX, pitch rate = superexpo(-x) * MC_ACRO_P_MAX,
expo = supexpo = 0 by default (linear); so y = p_cmd / R_MAX and x = -q_cmd / P_MAX.
"""
import math
from dataclasses import dataclass

import stick_profile

G = 9.81
PILOT_MODES = ("stabilized", "acro")
ACRO_R_MAX = math.radians(100.0)  # MC_ACRO_R_MAX PX4 default (the runner does not set it)
ACRO_P_MAX = math.radians(100.0)  # MC_ACRO_P_MAX PX4 default


def altitude_gains(thr0, bw_hz=0.25, zeta=0.8, pole_ratio=0.4):
    """(kp, ki, kd) from vertical accel = (g / thr0) dthr: char. poly (s + a)(s^2 + 2 zeta wn s + wn^2), a = pole_ratio * wn.

    thr = kp e + ki int(e) - kd (vz - vz_ref), K = g / thr0: s^3 + K kd s^2 + K kp s + K ki, hence
    kd = (2 zeta wn + a) / K, kp = (wn^2 + 2 zeta wn a) / K, ki = a wn^2 / K.
    """
    wn = 2.0 * math.pi * bw_hz
    a = pole_ratio * wn
    k = G / thr0
    return (wn * wn + 2 * zeta * wn * a) / k, a * wn * wn / k, (2 * zeta * wn + a) / k


@dataclass
class Corrections:
    thr: float = 0.0          # collective thrust correction, 0..1 units
    roll_stick: float = 0.0   # MANUAL_CONTROL y fraction, [-1, 1]
    pitch_stick: float = 0.0  # MANUAL_CONTROL x fraction, [-1, 1]


class Pilot:
    """One instance for the whole manual period (neutral and stick samples): state (integral, altitude reference) is never reset.

    Clamps scale with thr0 (F118): integral +-i_lim_k * thr0; total commanded thrust (base + correction) within [thr_min, thr_max]
    (the stick thrust range of stick_profile). Anti-windup: no integration while the output saturates in the error direction.
    """

    def __init__(self, mode, thr0, kp=None, ki=None, kd=None, k_level=1.5, bw_hz=0.25, zeta=0.8, i_lim_k=1.0,
                 thr_min=None, thr_max=None, r_max=ACRO_R_MAX, p_max=ACRO_P_MAX):
        self.mode, self.thr0, self.k_level, self.bw_hz, self.zeta = mode, thr0, k_level, bw_hz, zeta
        gk = altitude_gains(thr0, bw_hz, zeta)
        self.kp, self.ki, self.kd = (g if v is None else v for g, v in zip(gk, (kp, ki, kd)))
        self.i_lim = i_lim_k * thr0
        self.thr_min = stick_profile.MANTHR_MIN if thr_min is None else thr_min
        self.thr_max = stick_profile.THR_MAX if thr_max is None else thr_max
        self.r_max, self.p_max = r_max, p_max
        self.active = mode in PILOT_MODES
        self.integ = 0.0
        self.t_prev = None
        self.z_ref = None

    def params(self):
        return dict(mode=self.mode, thr0=self.thr0, kp=self.kp, ki=self.ki, kd=self.kd, k_level=self.k_level,
                    bandwidth_hz=self.bw_hz, damping=self.zeta, i_lim=self.i_lim, thr_min=self.thr_min,
                    thr_max=self.thr_max, acro_r_max_rad_s=self.r_max, acro_p_max_rad_s=self.p_max)

    def track(self, t, z_up_m, vz_up_mps, roll_rad, pitch_rad, vz_up_demand=0.0, thr_base=None):
        """Reference = altitude at the first call + integral of vz_up_demand (0 on neutral rows); then update()."""
        if self.z_ref is None:
            self.z_ref = z_up_m
        elif self.t_prev is not None:
            self.z_ref += vz_up_demand * min(max(t - self.t_prev, 0.0), 0.2)
        return self.update(t, z_up_m, vz_up_mps, roll_rad, pitch_rad, self.z_ref, vz_up_demand, thr_base)

    def update(self, t, z_up_m, vz_up_mps, roll_rad, pitch_rad, z_ref_m, vz_ref_mps=0.0, thr_base=None):
        if not self.active:
            return Corrections()
        base = self.thr0 if thr_base is None else thr_base
        dt = 0.0 if self.t_prev is None else min(max(t - self.t_prev, 0.0), 0.2)
        self.t_prev = t
        e = z_ref_m - z_up_m
        damp = -self.kd * (vz_up_mps - vz_ref_mps)
        lo, hi = self.thr_min - base, self.thr_max - base
        integ = min(self.i_lim, max(-self.i_lim, self.integ + self.ki * e * dt))
        thr = self.kp * e + integ + damp
        if (thr > hi and e > 0) or (thr < lo and e < 0):   # saturated in the direction of the error: hold the integral
            integ = self.integ
            thr = self.kp * e + integ + damp
        self.integ = integ
        c = Corrections(thr=min(hi, max(lo, thr)))
        if self.mode == "acro":
            c.roll_stick = min(1.0, max(-1.0, -self.k_level * roll_rad / self.r_max))
            c.pitch_stick = min(1.0, max(-1.0, self.k_level * pitch_rad / self.p_max))  # x = -q / P_MAX, q = -k pitch
        return c
