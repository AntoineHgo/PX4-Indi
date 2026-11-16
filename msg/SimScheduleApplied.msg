# Applied row of the simulation scenario schedule (SIMULATION ONLY)
#
# Published by sim_scenario_player (src/modules/simulation/sim_scenario_player) when it applies one row of the
# schedule file: arm/disarm and mode commands, offboard setpoint changes. Logged so that the instant a row took effect
# can be compared with the instant it was scheduled. Never published on real hardware.

uint64 timestamp          # [us] time since system start, taken when the row was applied (simulation time in SITL)
uint64 t_sched_us         # [us] time the row was scheduled for (first column of the schedule file)
uint32 row_index          # [-] zero-based index of the row among the data rows of the schedule file

uint8 kind                # [-] row kind
uint8 KIND_ARM = 1
uint8 KIND_DISARM = 2
uint8 KIND_MODE_OFFBOARD = 3
uint8 KIND_SP = 4

uint8 ORB_QUEUE_LENGTH = 8
