# Outer-loop jerk feed-forward body rates
#
# Published by mc_indi_pos_control with every attitude setpoint.
# mc_indi_rate_control adds roll and pitch to the rate setpoint while the message is fresh.

uint64 timestamp # [us] Time since system start

float32[3] omega_ff # [rad/s] [@frame FRD] Body rate feed-forward, z = 0
bool valid # INDI loop active (not bypass, landed, takeoff ramp or altitude only) and omega_ff finite
