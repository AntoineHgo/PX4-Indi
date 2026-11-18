# S81 stick-path stub notes
- Step 1 done: bench/stick_profile.py (pure generator), tests/test_stick_profile.py (self-test PASS), run_scenario.py --stick-mode
  {altctl,posctl,stabilized,acro}, scenarios.py stick_zsine_o6 (mode="stick"). Offboard/sched code paths not edited.
- Pre-test 1 (expo 0.6, 33 Hz pacing) found two issues: MPC_Z_MAN_EXPO default 0.6 gave gain 0.3; float pacing gave 33 Hz sticks. Fixed (STICK_PARAMS expo 0 dz 0; sim.sp_period). Re-flying 4 flights via fly.sh (old outputs overwritten).
- Run 2 failed: MPC_Z_MAN_EXPO/HOLD_DZ do not exist on this branch; expo 0.6 is hard-coded in src/lib/sticks/Sticks.hpp, deadzone is MAN_DEADZONE. Fix: MAN_DEADZONE 0, MPC_Z_VEL_MAX_DN 3, inverse expo in stick_profile. Re-flying 4.
