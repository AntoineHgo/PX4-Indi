# Torque produced by the measured actuator state
#
# Computed from ESC rpm telemetry in the units of vehicle_torque_setpoint: same expression as the allocated
# control of the torque setpoint, with the measured normalised thrust of each rotor,
# u_i = (omega_i / MC_INDI_W_MAX)^2, in place of the actuator setpoint.
# Only published while MC_INDI_W_MAX > 0.

uint64 timestamp # [us] Time since system start
uint64 timestamp_sample # [us] Oldest ESC telemetry sample (esc_status) used for this torque

float32[3] torque # [-] [@frame FRD] Measured normalised torque (roll, pitch, yaw)

bool valid # Every rotor of the first effectiveness matrix has a fresh, online, plausible rpm sample
uint8 motor_valid_mask # [-] Bit i set if the rotor with motor index i (Motor1 = bit 0, motors 1-8 only) has a valid sample
uint8 motor_frozen_mask # [-] Bit i set if the rpm of motor i is frozen (bit-identical while its command varied), treated as offline
