uint64 timestamp		# time since system start (microseconds)

# Outer-loop jerk feed-forward body rates, published by mc_indi_pos_control with every attitude setpoint
# mc_indi_rate_control adds roll and pitch to the rate setpoint while the message is fresh
float32[3] omega_ff		# rad/s, FRD body frame, z = 0
bool valid			# INDI stage active (not bypass, landed, ramp, z only) and omega_ff finite
