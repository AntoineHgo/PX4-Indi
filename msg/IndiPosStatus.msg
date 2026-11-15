uint64 timestamp		# time since system start (microseconds)

# Outer-loop INDI internals (published by mc_indi_pos_control while its external mode is active), NED world frame
float32[3] a_c			# commanded acceleration (m/s^2)
float32[3] a_f			# measured filtered acceleration (m/s^2)
float32[3] t_f			# measured filtered specific thrust vector (m/s^2)
float32[3] t_c			# commanded specific thrust vector after saturation (m/s^2)
float32[3] omega_ff		# body rate feedforward from the jerk reference (rad/s)
float32[4] q_d			# attitude setpoint from the commanded thrust vector and yaw, NAN while holding (logging only)

float32 mean_u			# mean normalised rotor thrust from the ESC rpm, NAN if not available
bool mean_u_valid		# the measured mean thrust was used in this cycle (else the model fallback)
float32 thrust			# normalised thrust command, thrust_body = (0, 0, -thrust)

uint8 JERK_SOURCE_FIELD = 0
uint8 JERK_SOURCE_DIFFERENCE = 1
uint8 jerk_source		# [@enum JERK_SOURCE] origin of the jerk reference

uint8 hold_cycles		# consecutive cycles in which the last setpoint was held (library rejected or stale input), 0 = normal
bool failure			# hold limit exceeded: a level attitude is commanded, the mode is failing
