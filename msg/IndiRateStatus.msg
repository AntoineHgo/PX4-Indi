uint64 timestamp		# time since system start (microseconds)

# INDI angular rate controller internals (published by mc_rate_control only while MC_RATE_CTL_TYPE selects INDI)
float32[3] nu				# desired angular acceleration (rad/s^2)
float32[3] angular_accel_filtered	# measured filtered angular acceleration used by the controller (rad/s^2)
float32[3] torque_filtered		# modelled actuator torque after the synchronisation filter (normalised)
float32[3] torque_increment		# commanded torque increment (normalised)

bool fault				# inputs or parameters were rejected in this cycle, the torque output is zero

bool measured_torque_in_use		# the measured actuator torque (ESC rpm) replaced the actuator model in this cycle
