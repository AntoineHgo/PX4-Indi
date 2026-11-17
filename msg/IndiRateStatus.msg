uint64 timestamp		# time since system start (microseconds)
uint64 timestamp_sample	# gyro sample time of the cycle (microseconds)

# INDI angular rate controller internals (published by mc_rate_control only while MC_RATE_CTL_TYPE selects INDI)
float32[3] nu				# desired angular acceleration (rad/s^2)
float32[3] angular_accel_filtered	# measured filtered angular acceleration used by the controller (rad/s^2)
float32[3] torque_filtered		# modelled actuator torque after the synchronisation filter (normalised)
float32[3] torque_increment		# commanded torque increment (normalised)
float32[3] lead_gain			# c_i applied this cycle (0 when landed)

bool fault				# inputs or parameters were rejected in this cycle, the torque output is zero

bool measured_torque_in_use		# the measured actuator torque (ESC rpm) replaced the actuator model in this cycle

# bench loop-break injection (MC_INDI_INJ_*), u = c + d is what is published and fed back; u == c while MC_INDI_INJ_AX is 0
float32[3] torque_sp_pre_inject		# c: INDI controller output (normalised torque)
float32[3] inject			# d: injected excitation (normalised torque)
float32[3] torque_sp			# u = c + d, before the non-finite guard of the published vehicle_torque_setpoint
