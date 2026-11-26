# INDI angular rate controller internals
#
# Published by mc_indi_rate_control.

uint64 timestamp # [us] Time since system start
uint64 timestamp_sample # [us] Gyro sample time of the cycle

float32[3] nu # [rad/s^2] [@frame FRD] Desired angular acceleration
float32[3] angular_accel_filtered # [rad/s^2] [@frame FRD] Measured filtered angular acceleration used by the controller
float32[3] torque_filtered # [-] [@frame FRD] Modelled actuator torque after the synchronisation filter (normalised)
float32[3] torque_increment # [-] [@frame FRD] Commanded torque increment (normalised)
float32[3] lead_gain # [-] [@frame FRD] Rate lead gain applied this cycle, 0 when landed
float32[3] rate_sp_dot # [rad/s^2] [@frame FRD] Filtered, clamped rate setpoint derivative used by the setpoint lead, 0 when landed

bool fault # Inputs or parameters were rejected in this cycle, the torque output is zero

bool measured_torque_in_use # The measured actuator torque (ESC rpm) replaced the actuator model in this cycle

# System identification excitation on the torque (MC_INDI_INJ_*):
# torque_sp = torque_sp_pre_inject + inject is published and fed back, equal to torque_sp_pre_inject while MC_INDI_INJ_AX is 0
float32[3] torque_sp_pre_inject # [-] [@frame FRD] INDI controller output (normalised torque)
float32[3] inject # [-] [@frame FRD] Injected excitation (normalised torque)
float32[3] torque_sp # [-] [@frame FRD] Sum of both, before the non-finite guard of the published vehicle_torque_setpoint

# System identification excitation on the rate setpoint (MC_INDI_INJ_PT 1), all zero otherwise
float32[3] rates_sp_pre_inject # [rad/s] [@frame FRD] Rate setpoint held in the module
float32[3] rates_sp_inject # [rad/s] [@frame FRD] Injected excitation
float32[3] rates_sp_applied # [rad/s] [@frame FRD] Rate setpoint the INDI controller received, sum of both

bool rate_sp_stale # No vehicle_rates_setpoint within MC_INDI_SP_TO while armed: rate setpoint zeroed, thrust held

bool foreign_torque_pub # A vehicle_torque_setpoint not published by this module was received (second rate controller)
