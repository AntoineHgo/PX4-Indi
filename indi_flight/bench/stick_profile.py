"""Stick profile for the runner's --stick-mode (S81, brief_rc_stub_s80.md): MANUAL_CONTROL samples from a trajectory.

Pure functions, no PX4 or MAVLink imports. In altctl / posctl the throttle stick is a vertical-velocity demand:
expo(stick) = vz_up / VZ_MAX_UP (MPC_Z_VEL_MAX_UP and _DN set to VZ_MAX_UP, MAN_DEADZONE 0, expo 0.6 inverted), so the z profile of a trajectory
(ZSINE_O6) becomes a stick profile. In stabilized / acro the throttle stick is thrust; the collective thrust demand
is thr = thr_hover + GAIN / 2 * demand, and the stick is the inverse of the PX4 map (S114 fix: S113 used the acro map
in stabilized too, which sent about MANTHR_MIN and the vehicle fell at the mode switch):
- acro (mc_rate_control / mc_indi_rate_control): thr = (stick + 1) / 2, so stick = 2 thr - 1;
- stabilized (mc_att_control throttle_curve, MPC_THR_CURVE default 0): piecewise linear through (-1, MPC_MANTHR_MIN),
  (0, hover thrust estimate), (1, MPC_THR_MAX), so centre stick = hover. thr_hover passed in is the runner's HTE read.
x / y / r (pitch, roll, yaw) stay neutral.
MANUAL_CONTROL fields: x pitch, y roll, r yaw in [-1000, 1000]; z throttle in [0, 1000] (500 = centre), see
mavlink_receiver.cpp handle_message_manual_control (throttle = z / 500 - 1).
"""

VZ_MAX_UP = 3.0         # m/s, MPC_Z_VEL_MAX_UP (PX4 default, set explicitly in the run)
THRUST_GAIN = 0.15      # stabilized / acro: throttle stick change per unit of demand (vz_up / VZ_MAX_UP)
STICK_EXPO = 0.6        # hard-coded in src/lib/sticks/Sticks.hpp (getThrottleZeroCenteredExpo), no parameter
VELOCITY_MODES = ("altctl", "posctl")
MANTHR_MIN = 0.08       # MPC_MANTHR_MIN default (multicopter_stabilized_mode_params.yaml), airborne value of the curve
THR_MAX = 1.0           # MPC_THR_MAX default (multicopter_position_control_limits_params.yaml)


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


# S136 G5.1 stick steps (GATES 5b): per axis in turn +A for HI_S, -A for LO_S, 0 for ZERO_S; MANUAL_CONTROL x pitch, y roll, r yaw.
STEP_AXES = (("roll", "y"), ("pitch", "x"), ("yaw", "r"))
STEP_HI_S, STEP_LO_S, STEP_ZERO_S = 0.5, 0.5, 2.5
STEP_AMP = {"acro": 1.0, "stabilized": 0.5}   # fraction of full stick (acro 100 deg/s; stabilized 0.5 x tilt / yaw-rate max)


def steps_duration():
    return len(STEP_AXES) * (STEP_HI_S + STEP_LO_S + STEP_ZERO_S)


def step_sticks(t, mode):
    """(x, y, r) ints at profile time t [s] of the G5.1 step sequence (zero outside it). Zero-order, edges at exact multiples."""
    out = {"x": 0, "y": 0, "r": 0}
    amp = int(round(STEP_AMP[mode] * 1000))
    t0 = 0.0
    for _, f in STEP_AXES:
        if t0 <= t < t0 + STEP_HI_S:
            out[f] = amp
        elif t0 + STEP_HI_S <= t < t0 + STEP_HI_S + STEP_LO_S:
            out[f] = -amp
        t0 += STEP_HI_S + STEP_LO_S + STEP_ZERO_S
    return out["x"], out["y"], out["r"]


def stick_sample(pva, t, mode, vz_max=VZ_MAX_UP, hover_thr=0.5, steps=False):
    """One sample at profile time t [s]: dict(x, y, z, r, throttle, vz_up_demand).

    pva(t) -> (pos, vel, acc) NED lists (run_scenario.traj_pva with the trajectory bound). The demand is the upward
    velocity of the profile; `throttle` is the decoded stick value actually sent (after int rounding), so the log is
    the applied value.
    """
    _, vel, _ = pva(t)
    vz_up = -vel[2]
    if steps:   # G5.1: throttle at the hover thrust stick (vz demand 0, pva zero), x / y / r from the step table
        smp = neutral_sample(mode, hover_thr)
        smp["x"], smp["y"], smp["r"] = step_sticks(t, mode)
        return smp
    if mode in VELOCITY_MODES:
        stick = inv_expo(vz_up / vz_max)  # PX4 applies expo 0.6 to the stick before scaling by MPC_Z_VEL_MAX_UP / _DN
    elif mode in ("stabilized", "acro"):
        stick = thrust_to_stick(hover_thr + 0.5 * THRUST_GAIN * vz_up / vz_max, mode, hover_thr)
    else:
        raise ValueError(mode)
    z = stick_to_raw(stick)
    return dict(x=0, y=0, z=z, r=0, throttle=raw_to_stick(z), vz_up_demand=vz_up)


def thrust_to_stick(thr, mode, hover_thr):
    """Throttle stick in [-1, 1] that PX4 maps to collective thrust thr in this manual-thrust mode (see module doc)."""
    if mode == "acro":
        return 2.0 * thr - 1.0
    if mode == "stabilized":
        # PX4 accepts hover in [0.05, 0.9] (also below MANTHR_MIN); only 0 / THR_MAX make the curve non-invertible
        if not 0.0 < hover_thr < THR_MAX:
            raise ValueError(f"hover thrust {hover_thr} outside (0, {THR_MAX}): curve not invertible")
        if thr >= hover_thr:
            return (thr - hover_thr) / (THR_MAX - hover_thr)
        if hover_thr <= MANTHR_MIN:  # curve never goes below hover: lower thrust unreachable, saturate at centre
            return 0.0
        return (thr - hover_thr) / (hover_thr - MANTHR_MIN)
    raise ValueError(mode)


def stick_to_thrust(stick, mode, hover_thr):
    """Forward PX4 map (for tests and log checks): acro linear, stabilized throttle_curve with MPC_THR_CURVE 0."""
    if mode == "acro":
        return 0.5 * (stick + 1.0)
    if mode == "stabilized":
        return hover_thr + stick * ((THR_MAX - hover_thr) if stick >= 0 else (hover_thr - MANTHR_MIN))
    raise ValueError(mode)


def neutral_sample(mode, hover_thr=0.5):
    """Centred sticks: zero climb rate in altctl / posctl, hover thrust in stabilized / acro."""
    z = 500 if mode in VELOCITY_MODES else stick_to_raw(thrust_to_stick(hover_thr, mode, hover_thr))
    return dict(x=0, y=0, z=z, r=0, throttle=raw_to_stick(z), vz_up_demand=0.0)
