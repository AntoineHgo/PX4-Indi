# A-45 cause search (S131), read-only

Edge = takeoff_status state 5 (flight) at t=34177500 us (INDI run), 34080000 (PID run).

Log evidence (INDI run, flight.ulg):
- vehicle_thrust_setpoint z: -0.1456 -> -0.1828 at the edge (one sample, +0.037); vehicle_attitude_setpoint thrust_body z steps at the same instant (-0.1456 -> -0.1828, -11 ms to 0 ms).
- vehicle_local_position_setpoint (published by the module in bypass): thrust z -0.1456 -> -0.1828, acceleration z -0.61 -> -3.28 at the edge. PID run: -0.1451 -> -0.1531, acceleration z -0.58 -> -1.15. Same params (MPC_Z_VEL_P_ACC 4, I 2, TKO_RAMP_T 3, hover 0.137), vz_sp ~ -0.78 and vz ~ -0.09/-0.10 in both.
- indi_pos_status: no sample until +180 ms after the edge (first: stage_mode 1, thrust 0.165, mean_u 0.1695, blend 0.001, mean_u_valid 1, t_c z -11.81). Before the edge it is not published (bypass). The 0.035 step therefore precedes the first INDI cycle.
- vehicle_land_detected: ground_contact 0, landed 0 at the edge. Hover estimate 0.1366 (no change).

Conclusion: NOT (a) (collective seed) and NOT (b) (integrator reset at handover): the stage is in Bypass (selectStageMode -> want=false, IndiStageMode.hpp:23-26; computeWantIndi needs takeoff flight && !ground_contact) when the step occurs, and the bypass branch (McIndiPosControl.cpp:353-364) publishes the stock setpoint unchanged. It is (c)/(d): the step is the stock PositionControl output at rampup end (acceleration setpoint -0.6 -> -3.3, i.e. ~P_acc*vz error 4*0.7 = 2.8 released when the rampup acceleration NaN-ing at McIndiPosControl.cpp:874-876 ends). In the PID run the same release gives only -1.15, so the INDI-module bypass differs from stock in what feeds PositionControl at that instant. I could not isolate that within the call budget; unverified candidates: (1) _control.resetIntegral() under want_indi (line ~968) vs stock; (2) the bypass-state integrator / _vel_int hover-thrust seeding differing with the 180 ms delayed want_indi; (3) timing of the edge relative to the ramp (INDI run z=-0.071, vz -0.092; PID z=+0.034).
The first INDI cycle itself is smooth: thrust 0.165 -> 0.1634 -> 0.1616 (+180..+203 ms) from the stock 0.183 (collective seeded from _coll_meas, line 358).

Next step (not done): diff MulticopterPositionControl.cpp vs McIndiPosControl.cpp around the rampup branch and log _vel_int/acc_sp at the edge.

Proposed minimal fix: none justified until the acc_sp difference (-3.28 vs -1.15) is traced; if the cause is a stock-vs-module setpoint divergence in bypass, make the bypass feed PositionControl exactly as stock (remove the divergence).
Test that would fail: SITL replay asserting |dthrust_z| at takeoff_status 4->5 differs by < 0.015 between MC_INDI_POS_EN=1 and 0 (now 0.037 vs 0.0075); extend indi_flight/bench/auto_smoke_check.py.
