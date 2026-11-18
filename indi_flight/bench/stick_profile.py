"""Stick profile for the runner's --stick-mode (S81, brief_rc_stub_s80.md): MANUAL_CONTROL samples from a trajectory.

Pure functions, no PX4 or MAVLink imports. In altctl / posctl the throttle stick is a vertical-velocity demand:
expo(stick) = vz_up / VZ_MAX_UP (MPC_Z_VEL_MAX_UP and _DN set to VZ_MAX_UP, MAN_DEADZONE 0, expo 0.6 inverted), so the z profile of a trajectory
(ZSINE_O6) becomes a stick profile. In stabilized / acro the throttle stick is thrust: stick = 2 thr_hover - 1 + GAIN
* demand (unverified shape, only a flight stub). x / y / r (pitch, roll, yaw) stay neutral.
MANUAL_CONTROL fields: x pitch, y roll, r yaw in [-1000, 1000]; z throttle in [0, 1000] (500 = centre), see
mavlink_receiver.cpp handle_message_manual_control (throttle = z / 500 - 1).
"""

VZ_MAX_UP = 3.0         # m/s, MPC_Z_VEL_MAX_UP (PX4 default, set explicitly in the run)
THRUST_GAIN = 0.15      # stabilized / acro: throttle stick change per unit of demand (vz_up / VZ_MAX_UP)
STICK_EXPO = 0.6        # hard-coded in src/lib/sticks/Sticks.hpp (getThrottleZeroCenteredExpo), no parameter
VELOCITY_MODES = ("altctl", "posctl")


def stick_to_raw(stick):
    """Throttle stick in [-1, 1] -> MANUAL_CONTROL z in [0, 1000] (int, clipped)."""
    return int(round(min(1.0, max(-1.0, stick)) * 500.0 + 500.0))


def raw_to_stick(z):
    """Inverse of stick_to_raw, as the PX4 receiver decodes it."""
    return z / 500.0 - 1.0


def expo(v, e=STICK_EXPO):
    """PX4 math::expo: the stick shaping of the manual vertical velocity, (1 - e) v + e v^3 (deadzone MAN_DEADZONE = 0)."""
    return (1.0 - e) * v + e * v ** 3


def inv_expo(d, e=STICK_EXPO):
    """Stick value in [-1, 1] whose expo() is d (clipped to +-1); expo is monotonic, bisection."""
    d = min(1.0, max(-1.0, d))
    lo, hi = -1.0, 1.0
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if expo(mid, e) < d else (lo, mid)
    return 0.5 * (lo + hi)


def stick_sample(pva, t, mode, vz_max=VZ_MAX_UP, hover_thr=0.5):
    """One sample at profile time t [s]: dict(x, y, z, r, throttle, vz_up_demand).

    pva(t) -> (pos, vel, acc) NED lists (run_scenario.traj_pva with the trajectory bound). The demand is the upward
    velocity of the profile; `throttle` is the decoded stick value actually sent (after int rounding), so the log is
    the applied value.
    """
    _, vel, _ = pva(t)
    vz_up = -vel[2]
    if mode in VELOCITY_MODES:
        stick = inv_expo(vz_up / vz_max)  # PX4 applies expo 0.6 to the stick before scaling by MPC_Z_VEL_MAX_UP / _DN
    elif mode in ("stabilized", "acro"):
        stick = 2.0 * hover_thr - 1.0 + THRUST_GAIN * vz_up / vz_max
    else:
        raise ValueError(mode)
    z = stick_to_raw(stick)
    return dict(x=0, y=0, z=z, r=0, throttle=raw_to_stick(z), vz_up_demand=vz_up)


def neutral_sample(mode, hover_thr=0.5):
    """Centred sticks: zero climb rate in altctl / posctl, hover thrust in stabilized / acro."""
    z = 500 if mode in VELOCITY_MODES else stick_to_raw(2.0 * hover_thr - 1.0)
    return dict(x=0, y=0, z=z, r=0, throttle=raw_to_stick(z), vz_up_demand=0.0)
