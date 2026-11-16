# Simulator ground truth, one sample per simulation step (SIMULATION ONLY)
#
# Published by the simulation bridge (gz_bridge) in the pose callback, from the same values as
# vehicle_attitude_groundtruth, vehicle_angular_velocity_groundtruth and vehicle_local_position_groundtruth.
# Those stock topics have a uORB queue of 1 and lose samples when logged at the simulation step rate;
# this topic has a deeper queue so that the logger can record every step. Never published on real hardware.

uint64 timestamp          # [us] time since system start
uint64 timestamp_sample   # [us] time of the simulator pose this sample was computed from

float32[4] q              # [-] Quaternion rotation from FRD body frame to NED earth frame (same as vehicle_attitude_groundtruth)
float32[3] angular_velocity # [rad/s] [@frame FRD] Angular velocity (same as vehicle_angular_velocity_groundtruth.xyz)

float32 x                 # [m] [@frame NED] North position
float32 y                 # [m] [@frame NED] East position
float32 z                 # [m] [@frame NED] Down position
float32 vx                # [m/s] [@frame NED] North velocity
float32 vy                # [m/s] [@frame NED] East velocity
float32 vz                # [m/s] [@frame NED] Down velocity

uint8 ORB_QUEUE_LENGTH = 16
