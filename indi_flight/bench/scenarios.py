"""Scenario table for the SITL benchmark runner (v0).

All durations are SIM seconds. Every scenario starts after the vehicle hovers at ~5 m in offboard mode.

mode:   "position"  -> hold the position/yaw captured at offboard start
        "attitude"  -> roll/pitch/yaw attitude setpoints (deg, yaw relative to initial yaw), thrust = hover
        "rate"      -> body-rate setpoints (deg/s), thrust = hover
axis:   which channel the segment values drive (roll | pitch | yaw | rollpitch = roll and pitch together)
segments: (name, duration_s, value). `settle` segments are not step events (value 0, lead-in);
          every other segment starts a step from the previous value to `value`.
"""
import math

STEP_DEG = 15.0
DIAG_STEP_DEG = 20.0
YAW_STEP_DEG = 45.0
RATE_STEP_DPS = 120.0

LEMNISCATE = dict(shape="lemniscate", ax=4.0, ay=2.0, w=5.0 / math.sqrt(32.0), laps=2, ramp_s=3.0)
CIRCLE_FAST = dict(shape="circle", r=4.0, z_amp=1.0, w=7.0 / 4.0, laps=3, ramp_s=3.0)
# Stage-8 outer-loop set O1-O7 (plan/s8_impl_spec.md sec. 5; new paths, never used for tuning; frozen in scenarios.md
# sec. 10 only after the O-13 pid_tuned pre-check). O1: Gerono lemniscate 10 m x 5 m, peak speed 6 m/s (at phi = 0 the
# speed is w sqrt(ax^2 + 4 ay^2)). O2: circle r 5 m at 5 m/s with a vertical sine of 1.5 m peak to peak (8 m/s and then
# 6.5 m/s were replaced after the O-13 pre-check: pid_tuned saturated 20 % / 7.6 % of the time and O5 crashed at both,
# collective thrust saturated by the circle plus the com_shift weight, results/s8i_o13_precheck.md).
# O6: vertical sine 2 m peak to peak, period 4 s (2.5 m/s^2 peak).
LEMNISCATE_O1 = dict(shape="lemniscate", ax=5.0, ay=2.5, w=6.0 / math.sqrt(50.0), laps=2, ramp_s=3.0)
CIRCLE_O2 = dict(shape="circle", r=5.0, z_amp=0.75, w=5.0 / 5.0, laps=3, ramp_s=3.0)
ZSINE_O6 = dict(shape="zmulti", harm=[1], amps=[1.0], w=math.pi / 2, laps=4, ramp_s=2.0)


def _traj_segments(traj, hold_s=3.0):
    return [("settle", 3.0, 0.0), ("traj", _traj_dur(traj), 0.0), ("hold", hold_s, 0.0)]


# Diagnostic vertical multisine (stage-8 finding 2, a_f / t_f lag identification): base period 4 s, harmonics 1, 3, 7, 13
# (0.25 to 3.25 Hz), each with an acceleration amplitude of about 0.8 m/s^2, 6 periods.
Z_MULTISINE = dict(shape="zmulti", harm=[1, 3, 7, 13], amps=[0.3, 0.036, 0.0066, 0.0019], w=math.pi / 2, laps=6,
                   ramp_s=2.0)


def _traj_dur(traj):
    return 2 * math.pi * traj["laps"] / traj["w"] + traj["ramp_s"]


def _attitude_steps(axis, amp, dur):
    return [
        ("settle", 2.0, 0.0),
        ("up", dur, +amp),
        ("zero1", dur, 0.0),
        ("down", dur, -amp),
        ("zero2", dur, 0.0),
    ]


def _rate_pulses(n=3):
    seq = [("settle", 2.0, 0.0)]
    for i in range(n):
        seq += [(f"pulse{i}_up", 0.25, +RATE_STEP_DPS), (f"pulse{i}_gap1", 2.0, 0.0),
                (f"pulse{i}_down", 0.25, -RATE_STEP_DPS), (f"pulse{i}_gap2", 2.0, 0.0)]
    return seq


SCENARIOS = {
    "hover": dict(mode="position", axis=None, segments=[("hold", 30.0, 0.0)]),
    "hover_long": dict(mode="position", axis=None, segments=[("hold", 60.0, 0.0)]),  # G2 margin windows (S40)
    "hover_xlong": dict(mode="position", axis=None, segments=[("hold", 150.0, 0.0)]),  # G2 xy cells, TP 20 x NP 5 (S87)
    "step_roll": dict(mode="attitude", axis="roll", segments=_attitude_steps("roll", STEP_DEG, 3.0)),
    # T9: plant mismatch, Ixx and Iyy x1.3 in the sim (controllers unchanged), T2 attitude step pattern.
    # model_variant: scale factors, see bench/model_variant.py (reused by held-out H5).
    "mismatch_inertia": dict(mode="attitude", axis="roll", segments=_attitude_steps("roll", STEP_DEG, 3.0),
                             model_variant=dict(ixx=1.3, iyy=1.3)),
    "step_pitch": dict(mode="attitude", axis="pitch", segments=_attitude_steps("pitch", STEP_DEG, 3.0)),
    "step_yaw": dict(mode="attitude", axis="yaw", segments=_attitude_steps("yaw", YAW_STEP_DEG, 4.0)),
    # Held-out H6: simultaneous roll and pitch steps.
    "step_diag": dict(mode="attitude", axis="rollpitch", segments=_attitude_steps("rollpitch", DIAG_STEP_DEG, 3.0)),
    "rate_step_roll": dict(mode="rate", axis="roll", segments=_rate_pulses(3)),
    # Held-out H5: combined plant mismatch (inertia x0.8 on all three axes, mass x1.15, motor time constants x2),
    # flown as two runs: the T2 attitude step pattern and the T4 rate pulses (D-h5).
    "mismatch_combined_att": dict(mode="attitude", axis="roll", segments=_attitude_steps("roll", STEP_DEG, 3.0),
                                  model_variant=dict(ixx=0.8, iyy=0.8, izz=0.8, mass=1.15, tau=2.0)),
    # Diagnostics for H5 (not part of the benchmark, never used for tuning): each H5 plant change on its own.
    "diag_h5_tau": dict(mode="attitude", axis="roll", segments=_attitude_steps("roll", STEP_DEG, 3.0),
                        model_variant=dict(tau=2.0)),
    "diag_h5_inertia": dict(mode="attitude", axis="roll", segments=_attitude_steps("roll", STEP_DEG, 3.0),
                            model_variant=dict(ixx=0.8, iyy=0.8, izz=0.8, mass=1.15)),
    "mismatch_combined_rate": dict(mode="rate", axis="roll", segments=_rate_pulses(3),
                                   model_variant=dict(ixx=0.8, iyy=0.8, izz=0.8, mass=1.15, tau=2.0)),
    # Trajectories (mode "trajectory"): the segment named "traj" flies a closed path from the hold position with
    # position, velocity and acceleration feedforward (bench/run_scenario.py traj_pva); other segments hold position.
    # T5: Gerono lemniscate 8 m x 4 m, peak speed 5 m/s (w = 5 / sqrt(32)), 2 laps.
    "traj_lemniscate": dict(mode="trajectory", axis=None, traj=LEMNISCATE,
                            segments=[("settle", 3.0, 0.0), ("traj", _traj_dur(LEMNISCATE), 0.0), ("hold", 3.0, 0.0)]),
    # Held-out H1: circle radius 4 m at 7 m/s (w = 1.75 rad/s) with a +-1 m vertical sine (2 m peak to peak), 3 laps.
    "traj_circle_fast": dict(mode="trajectory", axis=None, traj=CIRCLE_FAST,
                             segments=[("settle", 3.0, 0.0), ("traj", _traj_dur(CIRCLE_FAST), 0.0), ("hold", 3.0, 0.0)]),
    # Stage-8 set O (see LEMNISCATE_O1). Disturbances start with the path (dist_segment "traj"); the hold after the path
    # is long enough for the whole injector profile (gust_x 28 s, payload_add / com_shift 30 s).
    "o1_lemniscate": dict(mode="trajectory", axis=None, traj=LEMNISCATE_O1, segments=_traj_segments(LEMNISCATE_O1)),
    "o2_circle_z": dict(mode="trajectory", axis=None, traj=CIRCLE_O2, segments=_traj_segments(CIRCLE_O2)),
    "o3_lemniscate_gust": dict(mode="trajectory", axis=None, traj=LEMNISCATE_O1, disturbance="gust_x",
                               dist_segment="traj", segments=_traj_segments(LEMNISCATE_O1, 12.0)),
    "o4_lemniscate_payload": dict(mode="trajectory", axis=None, traj=LEMNISCATE_O1, disturbance="payload_add",
                                  dist_segment="traj", segments=_traj_segments(LEMNISCATE_O1, 13.0)),
    # O5 flies com_shift on the near-level vertical sine: the injector's world-fixed torque (level-hover approximation)
    # projects onto body yaw at the circle's 15-35 deg tilts and saturated yaw for pid_tuned (results/s8i_o13_precheck.md).
    "o5_zsine_com_shift": dict(mode="trajectory", axis=None, traj=ZSINE_O6, disturbance="com_shift",
                               dist_segment="traj", segments=_traj_segments(ZSINE_O6, 16.0)),
    "o6_zsine_mass": dict(mode="trajectory", axis=None, traj=ZSINE_O6, segments=_traj_segments(ZSINE_O6),
                          model_variant=dict(mass=1.15)),
    "o7_lemniscate_tau2": dict(mode="trajectory", axis=None, traj=LEMNISCATE_O1, segments=_traj_segments(LEMNISCATE_O1),
                               model_variant=dict(tau=2.0)),
    # Diagnostic only (outside the T/H/V sets, never used for tuning or a verdict): vertical excitation for the a_f / t_f
    # lag identification of INDI POS (bench/ident_s8_delay.py).
    "diag_z_multisine": dict(mode="trajectory", axis=None, traj=Z_MULTISINE,
                             segments=[("settle", 3.0, 0.0), ("traj", _traj_dur(Z_MULTISINE), 0.0), ("hold", 3.0, 0.0)]),
    # Held-out H4: motor 2 thrust x0.6 from the start of the T5 lemniscate.
    "motor_loss_2": dict(mode="trajectory", axis=None, traj=LEMNISCATE,
                         motor_fault=dict(segment="traj", motor=2, thrust_scale=0.6),
                         segments=[("settle", 3.0, 0.0), ("traj", _traj_dur(LEMNISCATE), 0.0), ("hold", 3.0, 0.0)]),
    # Disturbance scenarios (bench/disturbance.py). Position mode; the segment named "dist" starts the disturbance
    # profile (profile time 0 = start of that segment). The key `disturbance` selects the injector profile.
    # gust_x: profile 28 s = 2 ramp + 10 hold + 1 gust + 15 hold at 3 m/s. payload_add: step held 30 s.
    # inner-loop disturbance rejection: roll, pitch, yaw torque steps of 2 s each (disturbance.py torque_steps, 12 s)
    "torque_steps": dict(mode="position", axis=None, disturbance="torque_steps",
                         segments=[("settle", 5.0, 0.0), ("dist", 15.0, 0.0)]),
    "gust_x": dict(mode="position", axis=None, disturbance="gust_x",
                   segments=[("settle", 10.0, 0.0), ("dist", 28.0, 0.0)]),
    "payload_add": dict(mode="position", axis=None, disturbance="payload_add",
                        segments=[("settle", 10.0, 0.0), ("dist", 30.0, 0.0)]),
    # Held-out H2/H3, same structure as T6/T7 (profiles in bench/disturbance.py).
    "gust_diag": dict(mode="position", axis=None, disturbance="gust_diag",
                      segments=[("settle", 10.0, 0.0), ("dist", 27.6, 0.0)]),
    "com_shift": dict(mode="position", axis=None, disturbance="com_shift",
                      segments=[("settle", 10.0, 0.0), ("dist", 30.0, 0.0)]),
    # Plant fault (T8): attitude mode (level hold + yaw step). At the start of the segment named "loss" the runner sets
    # SIM_GZ_EC_MIN1/MAX1 (motor 0) to sqrt(scale) x their start value; omega = MIN + (MAX-MIN)*c and gz thrust ~ omega^2, so
    # thrust of motor 0 is `scale` x nominal at every command. Same plant change for every controller.
    # segments: 5 s settle, 10 s hold with the weak motor, 45 deg yaw step 4 s, back to 0 for 4 s.
    "motor_loss_0": dict(mode="attitude", axis="yaw", motor_fault=dict(segment="loss", motor=0, thrust_scale=0.7),
                         segments=[("settle", 5.0, 0.0), ("loss", 10.0, 0.0), ("up", 4.0, +YAW_STEP_DEG),
                                   ("zero", 4.0, 0.0)]),
}

# Stage-2 held-out set (plan/s2_heldout_v2.md, frozen in scenarios.md v2): run with --sim v2 only. Step pattern and rate
# pulses of H5, with one actuator or telemetry change each so that a loss is attributable. V7-V9 are H2, H3 and T8
# (gust_diag, com_shift, motor_loss_0) flown on the v2 configuration and need no new entry.
_ATT = dict(mode="attitude", axis="roll", segments=_attitude_steps("roll", STEP_DEG, 3.0))
_RATE = dict(mode="rate", axis="roll", segments=_rate_pulses(3))
_V_PLANT = {
    "tau2": dict(model_variant=dict(tau=2.0)),                                    # V1 slow actuator
    "asym": dict(model_variant=dict(tau_down=3.0)),                               # V2 slow spin-down
    "lat": dict(sim_params=dict(SIM_GZ_ERPM_LAT=2)),                              # V3 eRPM latency +2 frames
    "drop": dict(sim_params=dict(SIM_GZ_ERPM_DRP=0.2)),                           # V4 dropouts (+ total loss below)
}
for _k, _plant in _V_PLANT.items():
    SCENARIOS[f"v2_{_k}_att"] = {**_ATT, **_plant}
    SCENARIOS[f"v2_{_k}_rate"] = {**_RATE, **_plant}
# S81 manual-mode stick scenarios (run_scenario.py --stick-mode): the throttle stick follows the vertical velocity of
# ZSINE_O6 (altctl / posctl: vertical-velocity demand; stabilized / acro: thrust about hover), then a hold segment.
# Segment times are from the observed main mode. No --sched (runner streams MANUAL_CONTROL).
SCENARIOS["stick_zsine_o6"] = dict(mode="stick", axis=None, traj=ZSINE_O6,
                                   segments=[("settle", 3.0, 0.0), ("stick", _traj_dur(ZSINE_O6), 0.0), ("hold", 3.0, 0.0)])
SCENARIOS["v2_drop_att"]["erpm_loss"] = dict(motor=0, start="up", end="zero1")              # 3 s on motor 0
SCENARIOS["v2_drop_rate"]["erpm_loss"] = dict(motor=0, start="pulse1_up", end="pulse1_down")  # 2.25 s
_VIB3 = dict(sim_params=dict(SIM_GZ_VIB_ACC=3.0, SIM_GZ_VIB_GYR=0.15))           # V5 vibration x3
SCENARIOS["v2_vib3_hover"] = {**SCENARIOS["hover"], **_VIB3}
SCENARIOS["v2_vib3_att"] = {**_ATT, **_VIB3}
SCENARIOS["v2_sag_att"] = {**_ATT, "thrust_sag": dict(scale=0.85)}               # V6 thrust -15 % over the window

# Stage-2 held-out set V' (scenarios.md section 9, frozen for v3, run with --sim v2 only). Same patterns and hooks as V:
# W1/W2 = T8 segments with another motor / scale, W3 = motors 0 and 3 at 0.85 from "up" (motor_fault `motors` list),
# W4 = V6 hook at 75 %, W5 = V1 (tau x2 from the start) plus motor 2 at 0.8 from "up".
SCENARIOS["vp_loss1_06"] = {**SCENARIOS["motor_loss_0"], "motor_fault": dict(segment="loss", motor=1, thrust_scale=0.6)}
SCENARIOS["vp_loss2_08"] = {**SCENARIOS["motor_loss_0"], "motor_fault": dict(segment="loss", motor=2, thrust_scale=0.8)}
SCENARIOS["vp_gain03_att"] = {**_ATT, "motor_fault": dict(segment="up", motors=[0, 3], thrust_scale=0.85)}
SCENARIOS["vp_sag75_att"] = {**_ATT, "thrust_sag": dict(scale=0.75)}
SCENARIOS["vp_tau2_loss2_att"] = {**_ATT, **_V_PLANT["tau2"], "motor_fault": dict(segment="up", motor=2, thrust_scale=0.8)}

# Stage-5 slice 2 (S70): position-mode thrust gap. Offboard position hold, motors lose thrust at segment "up" and stay lost.
_S5_GAP = dict(mode="position", axis=None, segments=[("settle", 15.0, 0.0), ("up", 5.0, 0.0), ("hold", 40.0, 0.0)])
SCENARIOS["s5_gap085"] = {**_S5_GAP, "motor_fault": dict(segment="up", motors=[0, 1, 2, 3], thrust_scale=0.85)}
SCENARIOS["s5_loss08"] = {**_S5_GAP, "motor_fault": dict(segment="up", motor=2, thrust_scale=0.8)}

# Stage-5 P98: ALTCTL thrust gap. Neutral sticks (no "stick" segment), motors lose 15 % at "up" and stay lost (D-ALTCTL-Z).
SCENARIOS["s5_gap085_altctl"] = dict(mode="stick", axis=None, traj=ZSINE_O6,
                                     segments=[("settle", 15.0, 0.0), ("up", 5.0, 0.0), ("hold", 40.0, 0.0)],
                                     motor_fault=dict(segment="up", motors=[0, 1, 2, 3], thrust_scale=0.85))
# S103: same in manual POSCTL (fly with --stick-mode posctl), G5 pre-test of the position-mode thrust gap.
SCENARIOS["s5_gap085_posctl"] = {**SCENARIOS["s5_gap085_altctl"]}


# S131 AUTO smoke (mode "auto": navigator-driven, run_scenario.run_auto). `commander takeoff` to takeoff_alt, hold in loiter,
# optional mission (square, (north_m, east_m) from home), then RTL or land; the run ends at auto-disarm.
_AUTO_P = {"NAV_ACC_RAD": 2.0, "RTL_RETURN_ALT": 10.0, "RTL_DESCEND_ALT": 5.0, "RTL_LAND_DELAY": 0}
SCENARIOS["auto_tour"] = dict(mode="auto", axis=None, segments=[], auto=dict(
    takeoff_alt=5.0, hold_s=10.0, end="rtl", mission_max_s=120.0, post_mission_s=3.0,
    mission=[(20.0, 0.0), (20.0, 20.0), (0.0, 20.0), (0.0, 0.0)], params={**_AUTO_P, "MIS_TAKEOFF_ALT": 5.0}))
SCENARIOS["auto_land10"] = dict(mode="auto", axis=None, segments=[], auto=dict(
    takeoff_alt=10.0, hold_s=10.0, end="land", params={**_AUTO_P, "MIS_TAKEOFF_ALT": 10.0}))
