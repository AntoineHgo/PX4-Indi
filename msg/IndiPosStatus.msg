uint64 timestamp		# time since system start (microseconds)

# Outer-loop INDI internals (published by mc_indi_pos_control while its external mode is active), NED world frame
float32[3] a_c			# commanded acceleration, input of the INDI stage, including the bench excitation (m/s^2)
float32[3] a_c_pre_inject	# commanded acceleration before the bench excitation (m/s^2)
float32[3] inject		# bench excitation, MC_INDI_PINJ_* (m/s^2), 0 when off
float32[3] a_f			# measured filtered acceleration (m/s^2)
float32[3] t_f			# measured filtered specific thrust vector (m/s^2)
float32[3] t_c			# commanded specific thrust vector after saturation (m/s^2)
float32[3] t_c_applied		# specific thrust vector sent to the attitude setpoint, includes the excitation when MC_INDI_PINJ_PT is 1 (m/s^2)
float32[3] omega_ff		# body rate feedforward from the jerk reference (rad/s)
float32[4] q_d			# attitude setpoint from the commanded thrust vector and yaw, NAN while holding (logging only)

float32 mean_u			# mean normalised rotor thrust from the ESC rpm, NAN if not available
bool mean_u_valid		# the measured mean thrust was used in this cycle (else the model fallback)
float32 thrust			# normalised thrust command, thrust_body = (0, 0, -thrust)

float32 blend			# collective blend state (normalised thrust)
bool blend_hold			# blend is held because the vehicle is landed or maybe landed
bool blend_frozen		# blend was held in this cycle (landed, invalid telemetry or clamped collective)

uint8 JERK_SOURCE_FIELD = 0
uint8 JERK_SOURCE_DIFFERENCE = 1
uint8 jerk_source		# [@enum JERK_SOURCE] origin of the jerk reference

uint8 hold_cycles		# consecutive cycles in which the last setpoint was held (library rejected or stale input), 0 = normal
bool failure			# hold limit exceeded: a level attitude is commanded, the mode is failing

uint8 STAGE_MODE_BYPASS = 0
uint8 STAGE_MODE_INDI = 1
uint8 STAGE_MODE_INDI_MODEL_ACCEL = 2
uint8 STAGE_MODE_HOLD = 3
uint8 stage_mode		# [@enum STAGE_MODE] 1 indi (measured specific force), 2 indi on modelled specific force (ground, takeoff ramp or stale acceleration), 3 hold (0 never published)
