# Chatter probes S178 (one flight each, seed 1, baseline freeze7_s177/g4/cruise_typ_s1)
Command = baseline G4 cruise_typ_s1 (gate_g4.sh fly: runner --controller indi --model quad5in --seed 1 --speed 4 --sim v2 --gps-dly 110 --gnss-delay 110 --scenario traj_lemniscate --vib-acc 10 --vib-gyr 0 --imu-noise-scale 4.0), stream.sh, containers s178p1/s178p2. Scores: score/ (symlinks), rescore_key1.py + score_key2.py + chatter_cruise_s176.py (as G4_SCORES.md), chain_*.md (chatter_chain_s178.py).
Runner edit (owner rule F-9): env `INDI_SP_PERIOD` overrides sim.sp_period (default unchanged = SETPOINT_PERIOD 0.02), so P2 can be flown without touching the baseline path. Single flights: no seed-to-seed spread known, read ratios as indications.

## P1 p1_vel_lp8: MPC_VEL_LP 8 added to the freeze params (p1_params.params)
Verified read: McIndiPosControl.cpp:506-508 sets the filter, :749 `states.velocity.xy() = _vel_xy_lp_filter.update(...)` feeds the XY velocity P (:601 MC_INDI_XY_VP) (acceleration at :752 uses the same state).
Detector: CHATTER (key 1 and key 2), peaks 33.2 Hz (L1, 1.4e-3) and 20.1 Hz (L2, 2.1e-3 fixed band; 1.0e-3 old bins). Item 2 FAIL as the baseline.
L2d 18.7 Hz line RMS [baseline typ_s1 / P1 / PID]: motors diffB 2.0e-4 / 1.3e-4 / 8.5e-5; diffC 1.8e-4 / 1.3e-4 / 8.5e-5; a_c horizontal 3.5e-2 / 1.1e-2 / 2.6e-2; gyro 9.2e-4 / 6.7e-4 / 4.1e-4; torque_sp 2.6e-4 / 1.8e-4 / 1.2e-4.
Reading: part of the way (motors -35 %, a_c -69 %), not to PID; velocity P path contributes but is not the whole line. L1 collective unchanged (5.8e-4 vs 6.1e-4), as expected.

## P2 p2_sp10ms: INDI_SP_PERIOD=0.01 (sends 2139 vs 1112 in baseline), baseline params
Detector: CHATTER (key 1 and key 2). Flagged spans: L1 34.5-52.5 s peak 22.3 Hz (1.1e-3, key 2: 22.2 Hz, motors m0/m2/m3), L2 66-70 s 22.0 Hz (1.2e-3). The 33 Hz peak is no longer the detector max, a 22 Hz line is.
L1 33.5 Hz line RMS [baseline / P2 / PID]: motors collective 6.1e-4 / 2.6e-4 / 2.0e-4; a_c horizontal 6.5e-2 / 2.8e-2 / 1.5e-2 (lpos_sp); diffB 1.3e-4 / 4.1e-5 / 1.7e-5; diffC 8.9e-5 / 3.8e-5 / 1.2e-5; torque_sp 1.3e-4 / 5.3e-5; gyro 1.9e-4 / 1.5e-4.
Reading: the line did not vanish, it fell 2.3-2.4x and is still at 33.5 Hz (x234 over floor, collective), so the 30 ms sender is a main contributor (setpoint staircase supported) but not the only source: a 33 Hz line remains with a 10 ms sender (cause of remaining line open; the logged 89 Hz topics cannot exclude aliasing).
Side result (no change to L2 params): L2d motors diffB/C 18.7 Hz = 8.8e-5 / 8.6e-5 (baseline 2.0e-4/1.8e-4, PID 8.5e-5), a_c 3.5e-2 unchanged. So the L2 amplitude varies a lot flight to flight with changes not tied to the velocity filter; P1's L2 drop (1.3e-4) is inside that spread. Needs same-config repeats (seeds) before crediting MPC_VEL_LP.
