# Applied row of the simulation scenario schedule (SIMULATION ONLY)
#
# Published by sim_scenario_player (src/modules/simulation/sim_scenario_player) when it applies one row of the
# schedule file: arm/disarm and mode commands, offboard setpoint changes. Logged so that the instant a row took effect
# can be compared with the instant it was scheduled. Never published on real hardware.

uint64 timestamp          # [us] time since system start, taken when the row was applied (simulation time in SITL)
uint64 t_sched_us         # [us] time the row was scheduled for: first column, plus anchor_us for rows after an anchor
uint32 row_index          # [-] zero-based index of the row among the data rows of the schedule file

uint8 kind                # [-] row kind
uint8 KIND_ARM = 1
uint8 KIND_DISARM = 2
uint8 KIND_MODE_OFFBOARD = 3
uint8 KIND_SP = 4
uint8 KIND_SP_HOLD = 5        # sp captured from vehicle_local_position at apply time, see sp[]
uint8 KIND_ANCHOR = 6         # anchor condition met, rows after it are re-based on anchor_us
uint8 KIND_TAKEOFF = 7
uint8 KIND_LAND = 8
uint8 KIND_ATT = 9            # attitude setpoint stream, sp[] = roll, pitch, yaw (absolute), thrust (NAN = altitude PD)
uint8 KIND_PVA = 10           # position + velocity + acceleration setpoint, sp[] = x y z yaw (absolute NED)
uint8 KIND_SP_BACK = 11       # setpoint = position captured by the last sp_hold row

uint64 anchor_us          # [us] observed instant of the last anchor the row is based on, 0 before any anchor
float32[4] sp             # [m, m, m, rad] NED position and heading applied by KIND_SP / SP_HOLD / SP_BACK / PVA, [rad, rad, rad, -] by KIND_ATT, NAN otherwise

uint8 ORB_QUEUE_LENGTH = 8
