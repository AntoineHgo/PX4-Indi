# Paparazzi INDI reference notes

Clone commit: c04ffe40a035b997dc71e7d7965cbddb07606695 (Thu Nov 12 21:08:19 2026 +0100)
Path: indi_project/research/raw/paparazzi. S = sw/airborne/firmwares/rotorcraft/stabilization/
Other refs: F = sw/airborne/filters/low_pass_filter.h; module XML = conf/modules/stabilization_indi_simple.xml;
airframe example = conf/airframes/ENAC/quadrotor/bebop2_fish.xml. All line numbers are from files read in this session.

STATUS: complete (both controllers read in full).

======================================================================
PART A - stabilization_indi_simple.c  ("S/stabilization_indi_simple.c")
======================================================================
Runs inside the generic rotorcraft stabilization loop at PERIODIC_FREQUENCY (512 Hz assumed: stabilization_attitude_quat_int.c:208 comment; makefile defaults seen only in setup/demo/test_progs.makefile `?= 512` and
conf/firmwares/*.makefile `PERIODIC_FREQUENCY ?= 512`; ChibiOS test uses 500). Not a separate rate loop.

## A1. Control law
- Torque-space? NO: it is "command-space" per axis with a SCALAR effectiveness per axis (G1_p, G1_q, G1_r),
  units rad/s^2 per PPRZ command unit (MAX_PPRZ=9600, sw/airborne/paparazzi.h:8). No G1 matrix, no pseudo-inverse,
  no WLS. Output cmd[ROLL/PITCH/YAW] are then mixed to motors downstream by the (static) motor_mixing module.
- Rate loop is a pure P on rate error giving angular acceleration reference (L352-354):
    angular_accel_ref.p = (rate_sp.p - rates_filt.p) * indi.gains.rate.p;   (same for q, r)
  Default REF_RATE_{P,Q,R}=28 (module xml / bebop2_fish.xml:~157).
- Attitude loop (stabilization_indi_attitude_run L415-454): quaternion error -> att_fb = err quat vector part
  (optionally tilt/twist split if TILT_TWIST_CTRL, L428-439), then
    rate_sp.p = gains.att.p * att_fb.x / gains.rate.p;  (L443-445)   + feed-forward rates added (L447-449)
  then calls rate_run. Dividing by gains.rate makes the composite "parallel" PD:
  ang_acc_ref = Kp_att*att_err - Kd*rate  (+FF). Default REF_ERR_{P,Q,R}=600, REF_RATE=28.
  NOTE: no sqrt shaping / no accel limit in the controller itself; a reference model (quat_indi ref) is upstream.
- Yaw rate setpoint clipped: BoundAbs(rate_sp.r, indi.attitude_max_yaw_rate) (L349); default STABILIZATION_INDI_MAX_R
  = ATTITUDE_SP_MAX_R (L72-74). indi.max_rate (6 rad/s) is declared but not used in this file (grep'd, only L65,111).
- Increment equation (L360-362):
    du.p = 1.0 / g1.p * (angular_accel_ref.p - rate_d[0]);
    du.q = 1.0 / g1.q * (angular_accel_ref.q - rate_d[1]);
    du.r = 1.0 / (g1.r + g2) * (angular_accel_ref.r - rate_d[2] + g2 * du.r);   <- du.r on RHS is previous-step value
  Then u_in = u_filtered(o[0]) + du  (L375-377): the base is the FILTERED, actuator-model-propagated previous command,
  NOT the previous raw command, i.e. u_in = u_f + G1^-1 (nu - alpha_f).
- Thrust is NOT part of INDI: cmd[THRUST] = th_sp_to_thrust_i(thrust,...) passthrough (L400).

## A2. Angular acceleration estimation
- rate_d = finite difference of the OUTPUT of a 2nd-order Butterworth LPF on gyro rates, per axis:
    filter_pqr(indi.rate, body_rates) (L322); finite_difference_from_filter: (o[0]-o[1])*PERIODIC_FREQUENCY (L281-286, L325).
  i.e. first-order backward difference of the filtered signal, dt = 1/PERIODIC_FREQUENCY (fixed, not measured).
- Cut-off: STABILIZATION_INDI_FILT_CUTOFF default 8.0 Hz (L55-57); yaw can differ via FILT_CUTOFF_RDOT (default = FILT_CUTOFF, L60-62).
  tau=1/(2*pi*fc) (L219-221), fed to init_butterworth_2_low_pass(tau, Ts) -> biquad bilinear, Q=0.7071, K=tan(Ts/(2 tau)) = tan(pi fc Ts)
  (F:313-317, F:~165-170). So fc really is the -3 dB frequency. Example airframe bebop2_fish uses 3.2 Hz (very low) ; module xml doc example 8 Hz.
- Separate rate for FEEDBACK (not for acceleration): optional first-order LPF on gyro (rates_filt_fo), enabled only if
  FILT_CUTOFF_P/Q/R is defined (L80-96, L331-345); otherwise raw gyro rates used in the P term. Comment L327-329 warns the delay
  may require lower gains. Defaults if enabled via module xml: 30 Hz.

## A3. Actuator state (modelled, not measured)
- First-order actuator model, discrete, on the AXIS COMMAND (not on individual motors) (L315-317):
    u_act_dyn += act_dyn * (u_in_prev - u_act_dyn)
  act_dyn alpha = 1 - exp(-ACT_FREQ/PERIODIC_FREQUENCY) (L199-202), ACT_FREQ in rad/s (corner freq).
  Defaults: module xml 53.9 rad/s; bebop2_fish 31.7 rad/s -> alpha(512Hz) = 1-exp(-31.7/512)=0.060. No built-in default if undefined (only #warning L48-50).
  Old-style ACT_DYN_{P,Q,R} (alpha directly) deprecated (L43-47; warn text gives conversion -ln(1-a)*f).
- Synchronisation: u_act_dyn is passed through a Butterworth2 with the SAME cut-off as the gyro filter: filter_pqr(indi.u, &u_act_dyn)
  (L321 vs L322; both initialised with tau_axis[i], L226-227). u_filt = indi.u[i].o[0] is what is used as the INDI base (L375).
- Explicit delay: none (no transport delay / sample delay). The model pole + equal filtering is the only synchronisation mechanism.
- Note ordering: act model is propagated with u_in from PREVIOUS cycle first (L315), then filtered, then new du computed => u_in(k)
  is based on filtered model of u_in(k-1).

## A4. G2 / yaw spin-up
- Present for yaw only: g2 (STABILIZATION_INDI_G2_R). Yaw law L362 above: spin-up term g2 * du_r(prev) is added in numerator and
  (g1.r + g2) in denominator. I.e. models  alpha_r_dot-contribution ~ g1_r*du + g2*d(du)/dt discretised as g2*(du - du_prev)
  (g2 is effectively "per sample" gain, no explicit dt).
- Example values (module xml): G1_R=0.0022, G2_R=0.1450; bebop2_fish HW: G1_R=0.0025, G2_R=0.36; same airframe NPS/JSBSim: G2_R=0.0 because
  "rotor inertia is not modelled" (bebop2_fish.xml:~36).

## A5. Effectiveness adaptation (lms_estimation L462-504)
- Runs ONLY in the "not on ground with zero thrust" branch (L379-380): i.e. when (thrust>=300 || in_flight). It always runs the estimate,
  but only commits to indi.g1/g2 if indi.adaptive (L497-503). Default adaptive = FALSE (USE_ADAPTIVE; L140-144), compile #warning "Use caution" (L68-70).
- Signals: separate heavier filter set est.u / est.rate (2nd-order Butterworth, ESTIMATION_FILT_CUTOFF default 4.0 Hz, L76-78;
  module xml says 8.0) on u_act_dyn and gyro rates (L467-468). Take 1st derivative (rate_d, u_d) then 2nd derivative (rate_dd, u_dd)
  by finite differences (L471-478). So the regression is   rate_dd = g1 * u_d   (jerk vs command rate), i.e. high-pass-ish, offset-free.
- Update (L484-489), scaled by INDI_EST_SCALE=0.001 (L107) to avoid numerical problems; est.g1 stored as g1/0.001:
    g1.p -= (g1.p*du - rate_dd) * du * mu               (du = u_d*0.001)  [p, q]
    error = g1.r*du_r + g2*ddu - rate_dd_r ; g1.r -= error*du_r*mu/3 ; g2 -= error*1000*ddu*mu/3     (yaw: joint G1/G2, ddu = u_dd*0.001/f)
- Learning rate mu = STABILIZATION_INDI_ADAPTIVE_MU, example 0.0001 (module xml; bebop2_fish). Plain LMS (no normalisation, no RLS).
- Guards: lower clamp 0.01 on all of g1.p/q/r and g2 (L491-495) ("otherwise positive feedback"). No upper clamp, no dead-zone, no excitation check,
  no check on mu*|du|^2 stability. Estimation filters are only propagated in the flight branch -> filter state stale after ground phase (stabilization_indi_enter re-inits them).

## A6. Saturation / allocation / anti-windup
- No allocation in this controller: per-axis bound on total command (L383-394):
    default (FULL_AUTHORITY off): Bound(u_in.{p,q,r}, -4500, +4500)   i.e. +-47% of MAX_PPRZ 9600, leaving headroom for thrust
    FULL_AUTHORITY: p,q +-9600, r +-min(9600-|q|?, ...) (L387-389: rlim = 9600 - fabs(u_in.q); Bound(r,-rlim,rlim); then Bound(r,-9600,9600))
  Then cmd BoundAbs(MAX_PPRZ) (L403-406). Motor mixing downstream (outside scope) scales; actual motor saturation is not fed back into INDI.
- Anti-windup: implicit. u_in is clipped BEFORE being fed to the actuator model next step (u_act_dyn uses u_in, L315), so the base of the
  increment is the clipped command => no integrator windup ("the base is the actual last command"), but the clip is on axis commands, not
  on true motor outputs after mixing. Thrust headroom handled only by the 4500 limit. Yaw has no explicit lower priority except FULL_AUTHORITY rlim.

## A7. Mode transitions
- stabilization_indi_enter (L248-259): resets psi setpoint to current heading, zeros angular_accel_ref/u_act_dyn/u_in, re-inits all Butterworth
  filters with initial value 0.0 (indi_init_filters L216-238; init_butterworth_2_low_pass(...,0.0) i.e. gyro filter starts at 0 not at current rate;
  only the first-order feedback filter is initialised to current gyro, L235-237). Does NOT reset indi.du (du.r memory keeps old value) and does not reset est.* g/derivatives.
- On ground & thrust low (th_sp_to_thrust_i < 300 && !in_flight, L366-372): u_in = du directly (pure proportional on G1^-1*(ref-rate_d),
  no incremental accumulation), LMS skipped. Comment L364-365: otherwise "inputs will increment to the maximum before even getting in the air".
  Note: at this branch u_in is not based on u_filtered; the actuator model then sees u_in=du.
- Switch-in from another controller: only stabilization_indi_enter; no bumpless transfer of u (starts from 0 + du).

## A8. Discretisation / checks
- dt fixed = 1/PERIODIC_FREQUENCY (Butterworth built with sample_time=1/f, L223; finite diffs multiply by f L284, L298). If the loop jitters, derivative is wrong.
- NO NaN/isfinite checks anywhere in this file (grep'd). Division by g1/(g1+g2) unprotected except adaptive lower clamp 0.01 and settings min 0.001.
- Types: float math; commands int32 via implicit conversion to int32 at cmd assignment (L397-399).

## A9. Defaults (typical quad) - see module xml and bebop2_fish.xml
 G1 p/q/r = 0.0639/0.0361/0.0022 (module xml) ; Bebop2 real: 0.094/0.094/0.0025, G2_R 0.36 ; REF_ERR 600, REF_RATE 28 (all axes)
 FILT_CUTOFF 8 Hz (code default; bebop2_fish 3.2 Hz); ACT_FREQ 53.9 (xml) / 31.7 (bebop2_fish) rad/s ; ADAPTIVE_MU 1e-4; PERIODIC_FREQUENCY 512 Hz.
 Units: G1 in (rad/s^2)/PPRZ-unit with PPRZ in [-9600,9600] (commands not normalised).
 Observation: with Kp_att=600, Kd=28 -> att-loop omega_n = sqrt(600)=24.5 rad/s, zeta = 28/(2*24.5)=0.57 (my arithmetic, assuming ang_acc_ref = Kp e - Kd w).


======================================================================
PART B - stabilization_indi.c  (full controller; "S/stabilization_indi.c", header stabilization_indi.h)
======================================================================
Multi-actuator version: INDI_NUM_ACT actuators, INDI_OUTPUTS (3 moments + 1..3 thrust components). Writes per-ACTUATOR pprz commands
(actuators_pprz[], cmd[act_to_commands[i]], L811-815), so motor mixing is done inside INDI (G1 matrix), not by motor_mixing.

## B1. Control law
- Outer/inner structure identical to simple (default WEAK functions, can be overridden):
    rate controller L887-894:  accel_ref = (sp - rates_filt) * indi_gains.rate         (REF_RATE default 28)
    attitude controller L853-880: rates_ref = indi_gains.att * att_err_quat_vec / indi_gains.rate + rates_ff  (REF_ERR default 600)
  Gains defaults from conf/modules/stabilization_indi.xml:21-30: 600 / 28 all axes; MAX_R 120 deg/s (xml doc).
- Actuator-space with G1 matrix (INDI_OUTPUTS x INDI_NUM_ACT) allocation. Objective vector (L753-768):
    indi_v[0] = angular_accel_ref.p - dist_est[0];  indi_v[1] = ...q - dist_est[1];
    indi_v[2] = (angular_accel_ref.r - dist_est[2]) + g2_times_u;   indi_v[3] = v_thrust.z (and x,y for 5/6 outputs)
  where   dist_est = angular_acceleration(filtered) - B*u_filt  (L654-656, L626-627)  ["disturbance estimate"].
  Solve B u = v for ABSOLUTE u (not for a du):  u = B^+ (nu - alpha_f + B u_f) = u_f + B^+ (nu - alpha_f)  when unconstrained.
  So this is the classical INDI increment, written in a "disturbance estimate" form; the increment is implicit.
  Two allocators:
    (a) STABILIZATION_INDI_ALLOCATION_PSEUDO_INVERSE: indi_u[i] = sum_k g1g2_pseudo_inv[i][k]*indi_v[k] (L770-777; NOTE only 4 columns hard-coded);
        pinv = B^T (B B^T)^-1 via float_mat_inv_4d with x1000 scaling "there are numerical errors if the scaling is not right" (L1111-1149).
    (b) DEFAULT = WLS (L123-124, L778-789): wls_alloc(&wls_stab_p, Bwls, 0, 0, 10) -> max 10 active-set iterations (imax=10, L785).
- B = g1g2 = (G1 + G2 on yaw row)/INDI_G_SCALING (=1000) (sum_g1_g2 L1091-1104). Units: (rad/s^2) / PPRZ-unit per actuator.
  Example quad (conf/airframes/tudelft/bebop_indi_actuators.xml:116-121): G1_ROLL {20,-20,-20,20}, G1_PITCH {14,14,-14,-14}, G1_YAW {-1,1,-1,1},
  G1_THRUST {-.4,-.4,-.4,-.4}, G2 {-61.2,65.4,-65.7,65.5}  (all /1000 -> e.g. 0.020 rad/s^2 per count roll). Matches simple-version G1_P~0.08-0.094.

## B2. Angular acceleration estimation
- Same recipe as simple: 2nd-order Butterworth on gyro (measurement_lowpass_filters, STABILIZATION_INDI_FILT_CUTOFF), then backward difference of
  the filtered OUTPUT x PERIODIC_FREQUENCY (L639-645).   Examples: module xml doc 8 Hz (stabilization_indi.xml:35); bebop_indi_actuators.xml 5 Hz.
  No in-code default for FILT_CUTOFF in stabilization_indi.c (used unguarded at L525; I saw no #ifndef) -> must be set by airframe/module (unverified how the module system injects the doc default).
- Same gyro filter feeds ONLY accel estimate; feedback rate may be separately low-passed: first order (default) or 2nd-order Butterworth
  (FILTER_RATES_SECOND_ORDER) at FILT_CUTOFF_{P,Q,R} (20 Hz default, only active if airframe defines them: L49-65, L561-592). Runtime handler
  stabilization_indi_update_filt_freq (L503-517).
- Separate estimation filter (cutoff ESTIMATION_FILT_CUTOFF, 4-8 Hz) on gyro and on actuator state to get rate_dd and u_d, u_dd (L609-651) - these are
  updated every cycle even when not adapting (unlike simple).
- Body z accel (stateGetAccelBody_i) is also filtered and differentiated for the thrust-row adaptation (L1019-1029).

## B3. Actuator state
- Two modes (get_actuator_state L932-956):
    RPM_FEEDBACK=TRUE : actuator_state = act_obs, from ABI ACT_FEEDBACK: act_obs = (rpm - servo_min)*MAX_PPRZ/(servo_max-servo_min), clipped [0, MAX_PPRZ]
                        (L1153-1165). So RPM mapped LINEARLY into command units (no rpm^2 mapping, no latency compensation).
    else (default)    : first-order model per actuator (L943-944): actuator_state += act_dyn_discrete[i]*(indi_u[i]-actuator_state[i]); act_dyn_discrete = 1-exp(-ACT_FREQ/PERIODIC_FREQUENCY) (L432).
                        Optional per-cycle rate limit STABILIZATION_INDI_ACT_RATE_LIMIT (PPRZ/cycle) (L946-952, default only if defined).
  ACT_FREQ defaults (xml): 53.9 rad/s per actuator (alpha ~0.10 @512 Hz); no code default (L233 uses macro unguarded).
- Synchronisation: actuator_state is passed through Butterworth2 with SAME tau as the gyro filter (actuator_lowpass_filters, init L525, L537 vs gyro L531) (updated L609).
  The filtered state is used for B*u_f (L626); no explicit delay compensation anywhere (neither for RPM latency nor sensor delay).
- Uses the PREVIOUS cycle's indi_u as input of the model (the model is propagated at the start of rate_run, L606, before the new indi_u is computed).
- Observation: when motors are off the code sets indi_u = -MAX_PPRZ for motors (L806), so model state heads to -9600; effect on arm is mitigated because in_flight==false zeroes dist_est (L661-664).

## B4. G2 (spin-up) term
- Per-actuator G2 vector (scaled x1000, signs alternate with rotor spin direction), only on the yaw row (L1097-1101).
- Prediction: alpha_pred_yaw = B[2]*u_f(k) - g2.u_f(k-1)/1000  (L622, L627) => g1 u_f + g2 (u_f(k)-u_f(k-1)) i.e. a discrete derivative with no explicit dt (g2 absorbs per-sample).
- Command: indi_v[2] += g2.indi_u(prev)/1000 (L743, L756); combined with B[2] containing (g1+g2) this yields du = ... + g2*u_prev, same trick as simple (L362).
- Default G2 for real hardware in the example: ~ +-61..65 (x1000) vs G1_YAW +-1 ; G2 is ~60x G1 yaw, so spin-up dominates yaw dynamics there.

## B5. Adaptation (lms_estimation L1016-1085)
- Guard: `if (in_flight && indi_use_adaptive) lms_estimation();` (L792). Default indi_use_adaptive=FALSE (L82-84, USE_ADAPTIVE). Settings handler allows toggle.
- Regression on 2nd derivative of rate vs 1st derivative of actuator (both low-passed with ESTIMATION_FILT_CUTOFF 4-8 Hz):
    ddx_error_i = sum_j g1_est[i][j]*du_j (+ sum_j g2_est[j]*ddu_j for yaw) - ddx_i ;   g1_est[i][j] -= du_j * mu1[i] * ddx_error_i  (L992-995, L1041-1069)
  where du = actuator_state_filt_vectd*ADAPTIVE_MU, ddu = ..vectdd*ADAPTIVE_MU/PERIODIC_FREQUENCY (L1032-1033). ddx = {rate_dd p,q,r ; d/dt body-accel-z (thrust row)} (L1035).
- Learning rates: mu1 = {1e-5,1e-5,3e-6,2e-6} per axis (L264), mu2=0.002 for G2 (L266); ADAPTIVE_MU (code default 0.001, L86-88; airframes 1e-4) is used as an input scaling.
- Guards: (1) G1/G2 elements clamped to [g_init/2, 2*g_init] (INDI_ALLOWED_G_FACTOR=2.0, L47, bound_g_mat L1168-1210; sign-aware); (2) thrust row not adapted if |d(accel_z)/dt|>60 (rough landing, L1058-1063);
  (3) in_flight only. TODO in code: "only estimate when du_norm2 is large enough" (L1038) i.e. NO excitation check.
- After update: g1<-g1_est, g2<-g2_est, B recomputed, pseudo-inverse recomputed if enabled (L1075-1084).
- Per-actuator G (not just per-axis scalar), so row-wise LMS with all columns: plain LMS, no normalisation, no RLS.
- OBSERVATION (my reading, verify): prediction uses du scaled by ADAPTIVE_MU while ddx is unscaled and B uses /1000: scaling is only consistent if ADAPTIVE_MU==1/INDI_G_SCALING==1e-3.
  The airframes set 1e-4 -> predicted accel is 10x too small vs measured -> estimator would bias G upward until the 2x clamp hits. Probably masked by the clamp. Not run/tested here.

## B6. Saturation / allocation / anti-windup
- WLS (default): stabilization_indi_set_wls_settings (L901-923): u_min = -MAX_PPRZ for servos, 0 for motors; u_max = MAX_PPRZ; u_pref = act_pref (default 0) (L904-907).
  NOTE: bounds are ABSOLUTE actuator values (the comment says "min and max increments" but code is absolute), consistent with the absolute formulation (B1).
  Optional min throttle GUIDANCE_INDI_MIN_THROTTLE (hover/nav mode, airspeed-dependent for hybrid) as u_min for non-servos (L909-921).
- WLS cost (wls_alloc.c:177-188): minimise ||gamma_sq*Wv*(B u - v)||^2 + ||Wu*(u - u_pref)||^2, gamma_sq=10000 (L155).
  Priorities Wv default {1000,1000,1,100(,100)} = roll,pitch,yaw,thrust_z(,thrust_x) (L126-132), Wu default 1 (L135-137). So roll/pitch >> thrust >> yaw: yaw gives way first, thrust headroom is 10x weaker than roll/pitch.
  Active-set solver with imax=10 (L785); does not guarantee convergence (iter count is telemetered wls_u/wls_v).
- Post-WLS hard clip: servos BoundAbs MAX_PPRZ, motors Bound [0, MAX_PPRZ], motors off -> -MAX_PPRZ (L800-808). This clipped indi_u is what the actuator model sees next cycle => implicit anti-windup (the increment base is always the clipped command / measured RPM).
- No explicit integrator exists; the "windup" risk is in the disturbance-estimate path which is bounded by stablization_indi_yaw_dist_limit on yaw only (default 99999, i.e. effectively off; L105-107, L660, L747).
- Thrust: v_thrust.z = th_cmd * sum_i B[3][i] over thrust actuators (absolute thrust treated as acceleration; L712-728), or for THRUST_INCR_SP: incr + stab_thrust_filt (L694-700).
  Optional override V_THRUST_{X,Y,Z} (L731-739). cmd[COMMAND_THRUST] = mean of actuator_state over thrusters (L818-820).

## B7. Mode transitions
- stabilization_indi_enter (L497-501): only zeroes du_estimation/ddu_estimation. Deliberately does NOT reset inputs or filters (comment L489-495: unlikely to switch stabilization in flight; FIXME detect coming from non-INDI).
- Filters are initialised to 0.0 at init (init_filters L522-559) except first-order feedback filter which starts at current gyro.
- On ground (!in_flight): dist_est forced to zero (L661-664, L748-751) => u = B^+ nu (+thrust) i.e. no incremental memory; adaptation disabled (L792). Contrast with simple's `thrust<300 && !in_flight` check.
- Zero thrust: no special branch for thrust==0 in this file; WLS minimises ||u-u_pref|| (0) and thrust objective v_thrust=0 -> actuators sit at 0 + attitude demands, clipped at 0 for motors (WLS may then trade roll/pitch authority: see priorities).
- Motors off: motor commands -MAX_PPRZ (L806) and set_rotorcraft_commands zeroes (L964-979).

## B8. Discretisation
- Same fixed dt=1/PERIODIC_FREQUENCY everywhere; filters built with that sample time (L527); derivatives multiply by PERIODIC_FREQUENCY; no measured dt. 512 Hz assumed (see header of Part A).
- No NaN/isfinite checks (grep for isfinite/isnan in both files: no hits). Pseudo-inverse: no singularity check (float_mat_inv_4d). WLS has own conditioning via gamma_sq.
- Optional per-cycle actuator rate limit expressed per timestep (not per second) -> couples with loop rate (xml: ACT_RATE_LIMIT "depends on control frequency").

## B9. Defaults (example quad, tudelft/bebop_indi_actuators.xml:114-143)
 FILT_CUTOFF 5 Hz; ESTIMATION_FILT_CUTOFF 4 Hz; ACT_FREQ 53.9 rad/s x4; USE_ADAPTIVE TRUE, ADAPTIVE_MU 1e-4; WLS_PRIORITIES {1000,1000,1,100};
 REF_ERR 600 / REF_RATE 28; G1/G2 as in B1/B4. RPM_FEEDBACK TRUE on the real bebop target (:9), FALSE in NPS (:15).
 (att-loop: wn=sqrt(600)=24.5 rad/s, zeta=0.57; yaw adds MAX_R 120 deg/s limit in the simple version.)

======================================================================
10. WHAT TO COPY / WHAT TO DO DIFFERENTLY  (my interpretation, not facts about Paparazzi)
======================================================================
Copy:
 - Same-filter synchronisation: pass modelled/measured actuator state through the identical Butterworth2 as the gyro, take alpha = diff(filtered gyro)*f, and use the filtered actuator state as the INDI base (simple L321-325, L375; full L609-645).
 - Increment base = filtered, clipped actuator state (implicit anti-windup, since command is clipped before being fed back to the model).
 - First-order actuator model with continuous corner frequency parameter converted via 1-exp(-w/f) (simple L199-202); expose it in rad/s, not as alpha.
 - G2 spin-up handled as g2*(u(k)-u(k-1)) folded into effective effectiveness (g1+g2) for yaw (simple L362, full L622-756). It matters for real props (G2 ~ 60x G1 yaw in example).
 - Adaptation bounded to [g0/2, 2*g0] and disabled on ground / off by default; low-pass estimation filters much lower than control filters (4-8 Hz).
 - Ground/low-thrust: don't integrate increments (simple L366-372, full L661-664).
 - WLS priorities roll,pitch >> thrust >> yaw (full L126-132) as a template for headroom handling; absolute-u bounds with u_pref.
Do differently:
 - Use measured dt (or at least a guarded dt) and isfinite checks on filter outputs/G/alpha; Paparazzi has none and assumes 512 Hz.
 - Fully reset (to current gyro/actuator state) the filters and increment base on engage/arm; Paparazzi initialises Butterworth to 0.0 and does not reset in enter() in the full controller.
 - Do not clamp only the axis commands before mixing (simple L384-394): saturation after mixing is invisible to INDI; prefer allocation (WLS or priority-preserving desaturation) and feed the REAL post-allocation command into the actuator model.
 - Provide explicit delay/latency handling for RPM/ESC feedback and gyro group delay; Paparazzi has none besides the common filter, and its own comments say the feedback filter delay requires relaxed gains.
 - Avoid the mixed scaling of MU (learning-rate vs unit scaling, see B5 observation); use normalised LMS or RLS with a persistent-excitation check (Paparazzi TODO L1038), keep it off by default.
 - Thrust headroom: reserve explicit headroom for torque rather than using an arbitrary 4500/9600 axis limit or relying on weights alone.
 - Use physical units (rad/s^2 per normalised actuator, or per N*m) rather than raw PPRZ counts.
 - Consider a rate-loop-only design in PX4 (rate controller output = torque setpoint) and keep INDI as a replacement of the rate PID: Paparazzi uses a single P gain (28) on rate error with PD-from-attitude outside (att/rate ratio 600/28), i.e. no I-term and no D beyond what INDI provides.

======================================================================
11. UNVERIFIED / UNCLEAR
======================================================================
 - Rotorcraft PERIODIC_FREQUENCY default: only found `?= 512` in setup/demo/test_progs makefiles and a "assumed to be 512Hz" comment (stabilization_attitude_quat_int.c:208); did not find the rotorcraft makefile/board setting. Bebop ChibiOS-free Linux board may differ.
 - How/where FILT_CUTOFF, ESTIMATION_FILT_CUTOFF, ACT_FREQ get defaults for the full controller (module xml <define> in <doc> only documents; no #ifndef in .c). Not checked in the module-system build output.
 - Whether `in_flight` argument has any hysteresis/timing (determined by caller in autopilot; not read).
 - Upstream reference model (stabilization_attitude_quat_indi.c) not read; attitude setpoint shaping / rate limits live there.
 - The ADAPTIVE_MU scaling inconsistency (B5) is my reading of the code; not run.
 - Simple module xml kd settings for q/r point to REF_RATE_P as param name (cosmetic xml issue, L-~: stabilization_indi_simple.xml settings), not a code bug.
 - stabilization_indi_hinf.c / rate_indi.c not read (out of scope).
 - Gyro delay: stateGetBodyRates_f source (AHRS/IMU filtering, e.g. IMU low-pass) not examined; true total phase lag unknown.
