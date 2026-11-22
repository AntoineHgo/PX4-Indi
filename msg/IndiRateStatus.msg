uint64 timestamp		# time since system start (microseconds)
uint64 timestamp_sample	# gyro sample time of the cycle (microseconds)

# INDI angular rate controller internals (published by mc_indi_rate_control)
float32[3] nu				# desired angular acceleration (rad/s^2)
float32[3] angular_accel_filtered	# measured filtered angular acceleration used by the controller (rad/s^2)
float32[3] torque_filtered		# modelled actuator torque after the synchronisation filter (normalised)
float32[3] torque_increment		# commanded torque increment (normalised)
float32[3] lead_gain			# rate lead gain applied this cycle (0 when landed)
float32[3] rate_sp_dot			# filtered, clamped rate setpoint derivative used by the setpoint lead (rad/s^2, 0 when landed)

bool fault				# inputs or parameters were rejected in this cycle, the torque output is zero

bool measured_torque_in_use		# the measured actuator torque (ESC rpm) replaced the actuator model in this cycle

# bench excitation (MC_INDI_INJ_*): torque_sp = torque_sp_pre_inject + inject is published and fed back, equal to torque_sp_pre_inject while MC_INDI_INJ_AX is 0
float32[3] torque_sp_pre_inject		# INDI controller output (normalised torque)
float32[3] inject			# injected excitation (normalised torque)
float32[3] torque_sp			# sum of both, before the non-finite guard of the published vehicle_torque_setpoint

# bench excitation on the rate setpoint (MC_INDI_INJ_PT 1), all zero otherwise
float32[3] rates_sp_pre_inject		# rate setpoint held in the module (rad/s)
float32[3] rates_sp_inject		# injected excitation (rad/s)
float32[3] rates_sp_applied		# rate setpoint the INDI controller received, sum of both (rad/s)

bool rate_sp_stale			# no vehicle_rates_setpoint within MC_INDI_SP_TO while armed: rate setpoint zeroed, thrust held

bool foreign_torque_pub			# a vehicle_torque_setpoint not published by this module was received (second rate controller)
