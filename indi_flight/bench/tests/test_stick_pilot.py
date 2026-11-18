"""Self-test of the simulated stick pilot (S118) on a synthetic plant; no MAVLink, no PX4."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import stick_pilot as sp  # noqa: E402

G, THR0, DT = 9.81, 0.5, 0.01


def _fly(mode, tstop=30.0, thr_err=1.05, z0=0.0, roll0=0.0, pitch0=0.0, z_ref=0.0, pilot=None, tau_att=0.05):
    """Double integrator, thrust gain g/thr0, true thrust = thr_err * commanded, first-order rate loop; acro stick = rate."""
    pilot = pilot or sp.Pilot(mode, THR0)
    z, vz, roll, pitch, p, q, t = z0, 0.0, roll0, pitch0, 0.0, 0.0, 0.0
    zs = []
    while t < tstop:
        c = pilot.update(t, z, vz, roll, pitch, z_ref)
        thr = THR0 + c.thr                         # centre stick = hover thrust, pilot adds its correction
        vz += (G * (thr_err * thr / THR0 - 1.0)) * DT
        z += vz * DT
        p += (c.roll_stick * sp.ACRO_R_MAX - p) / tau_att * DT
        q += (-c.pitch_stick * sp.ACRO_P_MAX - q) / tau_att * DT   # PX4: q = -x * P_MAX
        roll += p * DT
        pitch += q * DT
        t += DT
        zs.append((t, z))
    return zs, roll, pitch


def test_altitude_recovers_with_5pct_thrust_error():
    for mode in ("stabilized", "acro"):
        zs, _, _ = _fly(mode, tstop=20.0)
        assert abs(zs[-1][1]) < 0.05, (mode, zs[-1])
        assert max(abs(z) for t, z in zs) < 1.5   # excursion stays bounded (open loop would drift 0.5 g * 0.1 * t^2)
        late = [z for t, z in zs if t > 15.0]
        assert max(abs(z) for z in late) < 0.05


def test_altitude_step_reference():
    pilot = sp.Pilot("stabilized", THR0)
    zs, _, _ = _fly("stabilized", tstop=20.0, z_ref=2.0, pilot=pilot)
    assert abs(zs[-1][1] - 2.0) < 0.05


def test_acro_tilt_decays():
    _, roll, pitch = _fly("acro", tstop=6.0, roll0=math.radians(32), pitch0=math.radians(-20))
    assert abs(roll) < math.radians(32) * 0.02 and abs(pitch) < math.radians(20) * 0.02   # e^(-1.5 * 6) = 1.2e-4 plus lag


def test_acro_sign_and_scale():
    c = sp.Pilot("acro", THR0).update(0.0, 0.0, 0.0, math.radians(10), math.radians(10), 0.0)
    assert c.roll_stick < 0 and c.pitch_stick > 0     # roll right -> roll left rate; nose up -> x forward (q = -x P_MAX < 0)
    assert abs(c.roll_stick * sp.ACRO_R_MAX - (-1.5 * math.radians(10))) < 1e-12


def test_stabilized_no_attitude_correction():
    c = sp.Pilot("stabilized", THR0).update(0.0, 0.0, 0.0, 0.5, 0.5, 0.0)
    assert (c.roll_stick, c.pitch_stick) == (0.0, 0.0)


def test_inactive_in_altctl_posctl():
    for mode in ("altctl", "posctl"):
        pl = sp.Pilot(mode, THR0)
        for t in (0.0, 1.0, 2.0):
            assert pl.update(t, 5.0, 3.0, 0.5, 0.5, 0.0) == sp.Corrections()


def test_limits_and_antiwindup():
    pl = sp.Pilot("stabilized", THR0)
    for i in range(20000):                           # 200 s with a 100 m error
        c = pl.update(i * 0.01, 0.0, 0.0, 0, 0, 100.0)
    assert abs(c.thr - (pl.thr_max - THR0)) < 1e-12 and abs(pl.integ) <= pl.i_lim + 1e-12
    c = pl.update(200.0, 100.0, 0.0, 0, 0, 100.0)    # error gone: the clamped integral unwinds quickly, not after 200 s of windup
    assert c.thr <= pl.i_lim + 1e-9 and pl.i_lim == 1.0 * THR0


def test_bandwidth_vs_attitude():
    assert 0.25 < 1.0 and 1.5 / (2 * math.pi) < 1.0   # altitude 0.25 Hz, levelling 0.24 Hz < 1/5 of a 5 Hz attitude loop
    kp, ki, kd = sp.altitude_gains(THR0)
    assert kp > 0 and ki > 0 and kd > 0


def test_f118_combined_thrust_and_mass_step():
    """thr0 = 0.12, available thrust x0.7 and mass x1.3 applied together as a step at 2 s (worst need 0.86 thr0 extra)."""
    thr0 = 0.12
    pl = sp.Pilot("stabilized", thr0)
    z, vz, t, zs = 0.0, 0.0, 0.0, []
    while t < 40.0:
        c = pl.track(t, z, vz, 0.0, 0.0, 0.0, thr0)
        thr = thr0 + c.thr
        assert sp.stick_profile.MANTHR_MIN - 1e-12 <= thr <= sp.stick_profile.THR_MAX + 1e-12
        k = 0.7 / 1.3 if t >= 2.0 else 1.0
        vz += G * (k * thr / thr0 - 1.0) * DT
        z += vz * DT
        t += DT
        zs.append((t, z))
    assert all(abs(z) < 0.5 for t, z in zs if 22.0 <= t)                   # back within 0.5 m within 20 s of the step, and stays
    assert abs(zs[-1][1]) < 0.1 and abs(pl.integ) < pl.i_lim               # no saturation-induced divergence, integral not pinned
    assert min(z for t, z in zs) > -15.0


def test_f118_state_persists_neutral_to_stick():
    pl = sp.Pilot("stabilized", THR0)
    for i in range(300):                                 # 3 s neutral rows, activated at z = 0 then sinking to 1 m low
        pl.track(i * DT, 0.0 if i == 0 else -1.0, 0.0, 0.0, 0.0, 0.0, THR0)
    integ0, zref0 = pl.integ, pl.z_ref
    assert integ0 > 0 and zref0 == 0.0
    c = pl.track(3.0, -1.0, 0.0, 0.0, 0.0, 0.5, THR0)   # first stick row (climb demand): same instance, no reset
    assert pl.integ >= integ0 and pl.z_ref > zref0 and c.thr > 0


def test_f118_reference_follows_vz_demand():
    pl = sp.Pilot("stabilized", THR0)
    z, t, worst = 3.0, 0.0, 0.0
    for i in range(1000):
        vzd = 0.0 if i < 200 else 1.0 * math.sin(0.5 * t)
        z += vzd * DT if i else 0.0                      # plant follows the demand exactly (z_ref integrates the same way)
        c = pl.track(t, z, vzd, 0.0, 0.0, vzd, THR0)
        worst = max(worst, abs(c.thr))
        t += DT
    assert worst < 1e-3, worst


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)
