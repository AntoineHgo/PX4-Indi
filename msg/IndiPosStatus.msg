# INDI acceleration loop internals
#
# Published by mc_indi_pos_control while it runs the INDI loop.

uint64 timestamp # [us] Time since system start

float32[3] a_c # [m/s^2] [@frame NED] Commanded acceleration, input of the INDI stage, including the system identification excitation
float32[3] a_c_pre_inject # [m/s^2] [@frame NED] Commanded acceleration before the system identification excitation
float32[3] inject # [m/s^2] [@frame NED] System identification excitation (MC_INDI_PINJ_*), 0 when off
float32[3] a_f # [m/s^2] [@frame NED] Measured filtered acceleration
float32[3] t_f # [m/s^2] [@frame NED] Measured filtered specific thrust vector
float32[3] t_c # [m/s^2] [@frame NED] Commanded specific thrust vector after saturation
float32[3] t_c_applied # [m/s^2] [@frame NED] Specific thrust vector sent to the attitude setpoint, includes the excitation when MC_INDI_PINJ_PT is 1
float32[3] omega_ff # [rad/s] [@frame FRD] Body rate feedforward from the jerk reference
float32[4] q_d # [-] Attitude setpoint quaternion from the commanded thrust vector and yaw, NaN while holding, logging only

float32 mean_u # [-] [@invalid NaN] Mean normalised rotor thrust from the ESC rpm
bool mean_u_valid # The measured mean thrust was used in this cycle (else the model fallback)
float32 thrust # [-] Normalised thrust command, thrust_body = (0, 0, -thrust)

float32 blend # [-] Collective blend state (normalised thrust)
bool blend_hold # Blend is held because the vehicle is landed or maybe landed
bool blend_frozen # Blend was held in this cycle (landed, invalid telemetry or clamped collective)

uint8 jerk_source # [@enum JERK_SOURCE] Origin of the jerk reference
uint8 JERK_SOURCE_FIELD = 0 # Jerk setpoint field of the trajectory setpoint
uint8 JERK_SOURCE_DIFFERENCE = 1 # Difference of the acceleration setpoint

uint8 hold_cycles # [-] Consecutive cycles in which the last setpoint was held (library rejected or stale input), 0 = normal
bool failure # Hold limit exceeded: a level attitude is commanded, the mode is failing

uint8 stage_mode # [@enum STAGE_MODE] INDI stage mode (0 is never published)
uint8 STAGE_MODE_BYPASS = 0 # Bypass
uint8 STAGE_MODE_INDI = 1 # INDI on the measured specific force
uint8 STAGE_MODE_INDI_MODEL_ACCEL = 2 # INDI on the modelled specific force (ground, takeoff ramp or stale acceleration)
uint8 STAGE_MODE_HOLD = 3 # Hold
