# T195 attitude outer-loop key: firmware source -> O(s)

L_total = L_att_indi * O, O(s) = 1 + N(s), N(s) = (Kv + Ki/s)(Kp + s)/s^2 + Kd*F(s)
Derivation: phi -> v = g*phi/s -> p = v/s; PositionControl.cpp:130 v_sp=Kp(p_sp-p); :150 a_sp=Kv(v_sp-v)+I-Kd*vdot;
tilt (:207-) body_z ~ -a_sp/g so phi_sp = a_sp/g (hover thrust does not enter tilt). y = att_p(phi_sp - phi) => O = 1+N.
Defaults (multicopter_position_control_gain_params.yaml): MPC_XY_P 0.95, VEL_P_ACC 1.8, VEL_I_ACC 0.4, VEL_D_ACC 0.2;
MPC_VELD_LP 5 Hz (params.yaml:73), MPC_VEL_LP 0 (disabled). No override in 4040_gz_quad5in (only THR_HOVER .137, MC_ROLL_P 8) or ax1_r800 params.
vel derivative: MulticopterPositionControl.cpp:333-336 (diff of filtered vel, then LP 5 Hz) ; F(s)=1/(1+s/(2pi*5)) (first-order approx).
INDI stage (McIndiPosControl.cpp:195-230, indi_accel_control.cpp:279-313): t_c = t_f + (a_c - a_f), accel_only=true.
 t_f = z_b*(-g_t*u_f) from ESC rpm (LPF 10 Hz, 1 sample dly), a_f = R*LPF(f_b)+g. Both are the same thrust vector through same filter,
 so t_f - a_f ~ -g (gravity feedforward) + mismatch (drag, model error, blend b). Small-signal: t_c = a_c - g + (mismatch). No 1.3 Hz cancel needed:
 increment adds no path except mismatch (drag*v term, UNVERIFIED size). Attitude from direction of t_c (thrustToAttitude).
Results (python, first-order filters, no EKF lag; "+ekf" = extra 50 ms delay on v,p):
fs   L_att alone fc/PM      L*O fc/PM       L*O(+50ms) fc/PM
267  1.19 / 70.4            1.39 / 55.3     1.28 / 52.6
400  1.19 / 71.4            1.38 / 56.4     1.28 / 53.6
800  1.19 / 72.4            1.38 / 57.5     1.27 / 54.7
|O|: 1.14@0.5Hz 1.19@1.3Hz 1.16@3Hz 1.05@10Hz; phase -31/-13/-9/-6 deg. => PM loss ~15 deg, fc +0.2 Hz.
UNVERIFIED: EKF vel lag/rate; mc_indi_pos_control runs on vehicle_local_position callback (hpp:142), same rate as pos control (not measured);
 position loop discrete delay; drag mismatch; PX4 LPF are 2nd-order biquad/1st-order alpha (used 1st order); yaw=0 assumed; MPC_ACC_DECOUPLE ignored.
