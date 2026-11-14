uint64 timestamp		# time since system start (microseconds)
uint64 timestamp_sample		# [us] Oldest ESC telemetry sample (esc_status) used for this torque

# Torque produced by the measured actuator state (ESC rpm), in the units of vehicle_torque_setpoint:
# same expression as the allocated control of the torque setpoint, with the measured normalised thrust of
# each rotor, u_i = (omega_i / CA_R_W_MAX)^2, in place of the actuator setpoint. Only published while CA_R_W_MAX > 0.
float32[3] torque		# [-] Measured normalised torque (roll, pitch, yaw)

bool valid			# every rotor of the first effectiveness matrix has a fresh, online, plausible rpm sample
uint8 motor_valid_mask		# bit i set if the rotor with motor index i (Motor1 = bit 0) has a valid sample
