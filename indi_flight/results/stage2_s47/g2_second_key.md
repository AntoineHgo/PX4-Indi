# MC_INDI_G2_Y derivation for quad5in (stage 2, S47)

Read-only derivation. Sources: `src/lib/indi_rate_control/indi_rate_control.hpp` (lines 52-53),
`indi_rate_control.cpp` (~360-390), `mc_indi_rate_control_params.yaml` (MC_INDI_G2_Y),
`indi_flight/sim/models/quad5in/model.sdf`, `indi_flight/sim/models/quad5in_base/model.sdf`,
`indi_flight/design/ref_airframe_check.md` (P9, M13, M17, M18), `indi_flight/results/stage2_s46/derive_g1.md`.

## Result

**G2_Y = 27.0 rad/s per (normalised yaw torque / s)**, same sign as G1_Y (= +205.3), using the
linear command-to-thrust convention of derive_g1 (T_i = T_max a_i). Equivalent ratio: G2_Y / G1_Y = 0.1317 s.

## Definitions (units)

- Law (hpp line 53): (G1 + G2/dt) dt_cmd = nu - a + (G2/dt)(t_f - t_f_prev). Since t_f is dimensionless, G2 has
  units (rad/s^2) x s = rad/s. Per unit of normalised torque RATE (1/s) it is rad/s^2.
- G1_Y: rad/s^2 per unit normalised yaw torque (cpp/derive_g1 convention, 0.55439 N m per unit / Izz).
- Plant model used: a_yaw = G1_Y t + G2_Y dt/dt, so the spin-up reaction is G2_Y * (rate of t) in rad/s^2.

## Inputs

| item | value | source |
|---|---|---|
| mass m | 0.61 kg | derive_g1 (0.566 base + 4 x 0.011) |
| rotors n | 4 | |
| Izz total | 2.7002e-3 kg m^2 | derive_g1 |
| kT (motorConstant) | 1.5e-6 N/(rad/s)^2 | model.sdf |
| km (momentConstant) | 0.01267 m | model.sdf, CA KM |
| hover fraction x_h | 0.13676 | derive_g1 |
| T_max per rotor | 10.939 N (= m g /(n x_h)) | derive_g1 |
| hover thrust per rotor | 1.49603 N (= m g /4) | = T_max x_h, consistent |
| rotorVelocitySlowdownSim s | 10 | model.sdf |
| rotor link izz (SDF) | 5e-5 kg m^2 | quad5in_base/model.sdf |

## Effective rotor inertia

The plugin commands the joint velocity to w/s (s = 10). The engine reacts with izz_link x d(w/s)/dt, so the
body sees izz_link/s x dw/dt = 5e-5 / 10 = **J_eff = 5.0e-6 kg m^2 per rotor**. This equals the real rotor spin
inertia J_r = 5e-6 that the design targets (P9 fix already in the SDF: izz 5e-5, ixx=iyy 2.5e-5, base izz 1.944e-3).
Why this value: the gyroscopic/spin-up reaction in gz is the link inertia times the joint acceleration, which
is the slowed-down speed, so the 1/s factor is cancelled by the 10x inertia; the body sees the real J_r w.

## Hover rotor speed

w_h = sqrt(T_h / kT) = sqrt(1.49603 / 1.5e-6) = **998.67 rad/s** (joint speed 99.87 rad/s). Matches P9/M17 value 998.7.

## Drag (G1) side

Yaw torque on body per motor = KM_i T_i (sign KM_i = [+,+,-,-]). Per unit normalised yaw command,
Mn_yaw = [+1,+1,-1,-1], so dT_i/du = T_max Mn_i and
dTau_yaw/du = sum_i KM_i Mn_i T_max = 4 km T_max = 4 x 0.01267 x 10.939 = **0.55439 N m**.
G1_Y = 0.55439 / 2.7002e-3 = **205.3** (matches derive_g1).

## Spin-up (G2) side

Rotor speed from thrust: dw/dT = 1/(2 kT w_h) at hover. Spin-up torque on body from rotor i:
sgn_i J_eff dw_i/dt, sgn_i = sign(KM_i). With dT_i/dt = T_max Mn_i du/dt:

dTau_spin/(du/dt) = sum_i sgn_i Mn_i J_eff T_max/(2 kT w_h) = 4 J_eff T_max/(2 kT w_h)
                  = 2 J_eff T_max/(kT w_h) = **0.07303 N m s**

(Using T_max = w_h^2 kT / x_h, this simplifies to 2 J_eff w_h / x_h = 2 x 5e-6 x 998.67 / 0.13676 = 0.07303.)

G2_Y = 0.07303 / Izz = 0.07303 / 2.7002e-3 = **27.05 -> 27.0**

Cross-check: G2/G1 = J_eff / (2 km kT w_h) = 5e-6 / (2 x 0.01267 x 1.5e-6 x 998.67) = 0.1317 s;
x 205.3 = 27.04. Consistent.

## Sign convention check

Body yaw torque from rotor i = sgn_i (Q_i + J dw_i/dt). Drag torque Q_i and spin-up reaction both come from the
motor torque that must drive both, so for the same command increment that accelerates the rotors (du/dt > 0)
the spin-up term ADDS to the drag-torque change: both sums are +4 (sgn_i Mn_i = +1 for all i). Hence G2_Y > 0,
same sign as G1_Y. Consistent with the law: the G2 term adds to G1 in the denominator.

## Scaling with operating rotor speed

- G2/G1 = J_eff / (2 km kT w_op), so it scales as **1/w_op** (at fixed allocation slope T_max).
- Full form: G2_Y = 2 J_eff T_max / (kT w_op Izz). At fixed x_h the hover form gives G2 = 2 J_eff w_h / (x_h Izz), i.e. grows with w_h.
  The two forms differ only in what is held fixed (allocation slope vs hover fraction). For a mass change at fixed
  kT, w_h ~ sqrt(m) and T_max ~ m, so G2 ~ sqrt(m) at fixed x_h.

## UNVERIFIED / caveats

1. **gz slowdown reaction sign and size not run.** P9 says "needs a gz run". The 1/s factor argument assumes the
   plugin sets the joint velocity directly, so the constraint reaction equals izz_link d(w/s)/dt. Not checked in logs.
2. **Thrust map mismatch (M18).** derive_g1 and this G2 assume T linear in the normalised command. With the default
   THR_MDL_FAC=0 the sim is quadratic in the command, dT/du = 2 T_h/x_h = 21.9 N (2x). Then G1_Y_sim ~ 411 and
   G2_Y_sim = 2 x 27.0 = **54.1** (ratio G2/G1 = 0.1317 s stays the same). Which value matches the plant depends
   on THR_MDL_FAC; the 27.0 is the value for the linear convention used by G1_Y = 205.
3. **Rotor lag.** The rotor first-order lag (tau 0.033 s) is assumed to be absorbed in t_f (actuator model); if the
   controller actuator lag differs, the spin-up reaction is only approximately G2 dt/dt.
4. **Yaw sign.** Assumes the gz turning direction and PX4 KM sign agree (derive_g1 flagged this unchecked).
5. **Param guidance conflict.** mc_indi_rate_control_params.yaml says G2 should be "of the order of G1_Y times the
   loop period (about 0.02)", i.e. ~4 here. The physics gives G2/G1 = 0.13 s, i.e. ~27. The yaml heuristic looks
   wrong for this airframe by about 6.5x; treat the derived value as the candidate, to be checked by a gz step test.
6. Not checked: whether the rotor link's own spin reaction also enters base_link inertia (M13 assumed it does
   through the Izz total 2.7002e-3).
